import json
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum
from django.middleware.csrf import get_token as csrf_get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

from apps.orders.models import Order
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, 
    IncidenceSerializer
)
from .permissions import IsDeliveryUser
from apps.orders.constants import MESSAGE_ORDER_NOT_FOUND_OR_ASSIGNED

logger = logging.getLogger(__name__)


class DeliveryOrdersAPIView(APIView):
    """
    HU-033: Lista de pedidos asignados al entregador
    GET /api/delivery/orders/
    """
    permission_classes = [IsAuthenticated, IsDeliveryUser]
    throttle_classes = [UserRateThrottle]
    
    def get(self, request):
        user = request.user
        today = timezone.localdate()

        # Obtener pedidos asignados al usuario que:
        # 1. Están pendientes activos (listo o en camino)
        # O 2. Fueron completados o cancelados hoy (acción realizada hoy)
        orders = Order.objects.filter(
            Q(assigned_delivery_user=user) &
            (Q(status__in=['listo', 'en_camino']) | Q(status__in=['entregado', 'cancelado'], updated_at__date=today))
        ).order_by('-created_at')

        # Filtros enviados por el frontend
        filter_param = request.query_params.get('filter', 'all')

        if filter_param == 'pending':
            # Por entregar (listo o en camino)
            orders = orders.filter(status__in=['listo', 'en_camino'])
        elif filter_param == 'completed':
            # Entregados hoy
            orders = orders.filter(status='entregado')

        serializer = OrderListSerializer(orders, many=True)

        return Response({
            'success': True,
            'count': orders.count(),
            'orders': serializer.data,
            'last_update': timezone.now().isoformat(),
        })


class DeliveryOrderDetailAPIView(APIView):
    """
    HU-034, HU-035: Detalle de un pedido específico
    GET /api/delivery/orders/<int:order_id>/
    """
    permission_classes = [IsAuthenticated, IsDeliveryUser]
    throttle_classes = [UserRateThrottle]
    
    def get(self, request, order_id):
        user = request.user
        
        try:
            order = Order.objects.get(
                id=order_id,
                assigned_delivery_user=user
            )
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': MESSAGE_ORDER_NOT_FOUND_OR_ASSIGNED
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrderDetailSerializer(order)
        
        # Obtener incidencia previa si existe (desde cancelled_reason)
        incidence = None
        if order.cancelled_reason:
            try:
                incidence = json.loads(order.cancelled_reason)
            except json.JSONDecodeError:
                incidence = {
                    'type': 'unknown',
                    'comments': order.cancelled_reason,
                    'reported_at': order.updated_at.isoformat()
                }
        
        return Response({
            'success': True,
            'order': serializer.data,
            'incidence': incidence,
            'actions': {
                'can_confirm_delivery': order.status == 'en_camino',
                'can_report_incidence': order.status not in ['entregado', 'cancelado'],
                'can_cancel': order.status not in ['entregado', 'cancelado'],
            }
        })


class DeliveryMarkAsPaidAPIView(APIView):
    """
    HU-034: Confirmar entrega de un pedido
    Todos los pedidos son pre-pagados vía Stripe.
    El repartidor solo confirma la entrega física.
    POST /api/delivery/orders/<int:order_id>/mark-paid/
    """
    permission_classes = [IsAuthenticated, IsDeliveryUser]
    throttle_classes = [UserRateThrottle]

    def post(self, request, order_id):
        user = request.user

        try:
            order = Order.objects.get(
                id=order_id,
                assigned_delivery_user=user
            )
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': MESSAGE_ORDER_NOT_FOUND_OR_ASSIGNED
            }, status=status.HTTP_404_NOT_FOUND)

        if order.status == 'entregado':
            return Response({
                'success': False,
                'message': 'Este pedido ya fue confirmado como entregado.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if order.status != 'en_camino':
            return Response({
                'success': False,
                'message': f'Solo puedes confirmar entregas en estado "En camino". '
                           f'Estado actual: {order.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            order.mark_as_delivered(user=user)

            logger.info(
                "Pedido %s confirmado como entregado por %s",
                order.order_number, user.username
            )

            return Response({
                'success': True,
                'message': f'Pedido {order.order_number} confirmado como entregado.',
                'order_id': order.id,
                'order_number': order.order_number,
                'delivered_at': timezone.now().isoformat(),
            })
        except Exception as exc:
            logging.exception("Error al confirmar entrega del pedido %s: %s", order.id, exc)
            return Response({
                'success': False,
                'message': 'Error al confirmar la entrega.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeliveryIncidenceAPIView(APIView):
    """
    HU-038: Registrar incidencia
    POST /api/delivery/orders/<int:order_id>/incidence/
    """
    permission_classes = [IsAuthenticated, IsDeliveryUser]
    throttle_classes = [UserRateThrottle]
    
    def post(self, request):
        user = request.user
        order_id = request.data.get('order_id')

        if not order_id:
            return Response({
                'success': False,
                'message': 'Se requiere order_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar datos (fuera del bloque atómico)
        serializer = IncidenceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        action = data.get('action', 'report')

        # Construir objeto incidencia
        incidence_data = self._build_incidence_data(serializer, data, user, action)

        try:
            with transaction.atomic():
                order = self._get_order(order_id, user)

                # Validar que el pedido no esté entregado o cancelado
                validation_error = self._validate_order_not_final(order)
                if validation_error:
                    return validation_error

                if action == 'cancel':
                    return self._cancel_order(order, incidence_data, user)
                return self._report_incidence(order, incidence_data)

        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': MESSAGE_ORDER_NOT_FOUND_OR_ASSIGNED
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logging.exception(f"Error al reportar incidencia en pedido {order_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error interno al procesar la incidencia'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _build_incidence_data(self, serializer, data, user, action):
        return {
            'type': data['incidence_type'],
            'type_label': dict(serializer.fields['incidence_type'].choices).get(data['incidence_type'], ''),
            'comments': data.get('comments', ''),
            'reported_by': user.id,
            'reported_by_name': user.get_full_name() or user.username,
            'reported_at': timezone.now().isoformat(),
            'action_taken': action,
        }

    def _get_order(self, order_id, user):
        return Order.objects.select_for_update().get(
            id=order_id,
            assigned_delivery_user=user
        )

    def _validate_order_not_final(self, order):
        if order.status in ['entregado', 'cancelado']:
            return Response({
                'success': False,
                'message': f'No se puede reportar incidencia en pedido con estado: {order.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        return None

    def _cancel_order(self, order, incidence_data, user):
        reason = json.dumps(incidence_data, ensure_ascii=False)
        order.cancel(reason, user=user)
        logger.info(f"Pedido {order.order_number} cancelado por incidencia: {incidence_data['type']}")

        return Response({
            'success': True,
            'message': f'Pedido {order.order_number} cancelado por: {incidence_data["type_label"]}',
            'order_id': order.id,
            'order_number': order.order_number,
            'status': 'cancelado',
            'incidence': incidence_data,
        })

    def _report_incidence(self, order, incidence_data):
        existing_incidences = []
        if order.cancelled_reason:
            try:
                existing = json.loads(order.cancelled_reason)
                if isinstance(existing, list):
                    existing_incidences = existing
                elif isinstance(existing, dict):
                    existing_incidences = [existing]
            except json.JSONDecodeError:
                pass

        existing_incidences.append(incidence_data)
        order.cancelled_reason = json.dumps(existing_incidences, ensure_ascii=False)
        order.save(update_fields=['cancelled_reason', 'updated_at'])

        # Enviar notificación al admin (implementar después)
        # send_admin_notification(order, incidence_data)

        logger.info(f"Incidencia {incidence_data['type']} reportada en pedido {order.order_number}")

        return Response({
            'success': True,
            'message': f'Incidencia reportada: {incidence_data["type_label"]}',
            'order_id': order.id,
            'order_number': order.order_number,
            'status': order.status,
            'incidence': incidence_data,
        })


class DeliverySummaryAPIView(APIView):
    """
    HU-036: Resumen diario de entregas
    GET /api/delivery/summary/
    """
    permission_classes = [IsAuthenticated, IsDeliveryUser]
    throttle_classes = [UserRateThrottle]
    
    def get(self, request):
        user = request.user
        today = timezone.localdate()
        
        # Pedidos entregados hoy (independientemente de cuándo fueron creados)
        delivered_orders = Order.objects.filter(
            assigned_delivery_user=user,
            status='entregado',
            updated_at__date=today
        )
        total_delivered = delivered_orders.count()
        total_amount = delivered_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Pedidos actualmente pendientes (en estado listo o en camino)
        pending_orders = Order.objects.filter(
            assigned_delivery_user=user,
            status__in=['listo', 'en_camino']
        )
        pending_count = pending_orders.count()
        pending_amount = pending_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Pedidos con incidencias reportadas hoy (estatus cancelado, actualizados hoy, con cancelled_reason no vacía)
        incidences_orders = Order.objects.filter(
            assigned_delivery_user=user,
            status='cancelado',
            updated_at__date=today
        ).exclude(
            cancelled_reason=''
        ).exclude(
            cancelled_reason__isnull=True
        )
        
        # Incidencias del día
        incidences = []
        for order in incidences_orders:
            try:
                data = json.loads(order.cancelled_reason)
                entries = data if isinstance(data, list) else [data]
                for inc in entries:
                    incidences.append({
                        'order_id': order.id,
                        'order_number': order.order_number,
                        'type': inc.get('type_label', 'Desconocida'),
                        'comments': inc.get('comments', ''),
                        'reported_at': inc.get('reported_at', order.updated_at.isoformat()),
                    })
            except json.JSONDecodeError:
                continue
        
        summary = {
            'date': today.isoformat(),
            'total_delivered': total_delivered,
            'total_paid': total_delivered,  # Todos los entregados se asumen pagados (pre-pagados)
            'total_amount': str(total_amount),
            'pending_payment': 0,  # No hay cobro contra entrega
            'pending_delivery': pending_count,
            'pending_amount': str(pending_amount),
            'delivered_orders': [
                {
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer': order.customer_name,
                    'amount': str(order.total_amount),
                    'paid': True,
                }
                for order in delivered_orders
            ],
            'incidences': incidences,
        }
        
        return Response({
            'success': True,
            'summary': summary,
        })


@require_GET
@ensure_csrf_cookie
def get_csrf_token(request):
    """Devuelve un token CSRF fresco para el PWA."""
    return JsonResponse({'csrfToken': csrf_get_token(request)})