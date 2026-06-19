from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from datetime import date, timedelta
import json
import logging

from apps.orders.models import Order
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, 
    OrderSummarySerializer, MarkAsPaidSerializer,
    IncidenceSerializer
)
from .permissions import IsDeliveryUser

logger = logging.getLogger(__name__)
User = get_user_model()


class DeliveryOrdersAPIView(APIView):
    """
    HU-033: Lista de pedidos asignados al entregador
    GET /api/delivery/orders/
    """
    permission_classes = [IsAuthenticated, IsDeliveryUser]
    
    def get(self, request):
        user = request.user
        today = date.today()
        
        # Obtener pedidos asignados al usuario en estados activos
        orders = Order.objects.filter(
            assigned_delivery_user=user,
            status__in=['listo', 'en_camino']
        ).exclude(
            status='entregado'
        ).order_by('-created_at')
        
        # Filtrar por fecha de creación (pedidos de hoy)
        orders_today = orders.filter(
            created_at__date=today
        )
        
        # Si no hay pedidos de hoy, mostrar todos los pendientes
        if not orders_today.exists():
            orders = orders
        else:
            orders = orders_today
        
        # Aplicar filtros desde query params
        filter_param = request.query_params.get('filter', 'all')
        
        if filter_param == 'pending':
            orders = orders.filter(is_paid=False)
        elif filter_param == 'completed':
            orders = orders.filter(is_paid=True)
        
        serializer = OrderListSerializer(orders, many=True)
        
        return Response({
            'success': True,
            'count': orders.count(),
            'orders': serializer.data,
            'filters': {
                'all': OrderListSerializer(orders, many=True).data,
                'pending': OrderListSerializer(
                    orders.filter(is_paid=False), many=True
                ).data,
                'completed': OrderListSerializer(
                    orders.filter(is_paid=True), many=True
                ).data,
            },
            'last_update': timezone.now().isoformat(),
        })


class DeliveryOrderDetailAPIView(APIView):
    """
    HU-034, HU-035: Detalle de un pedido específico
    GET /api/delivery/orders/<int:order_id>/
    """
    permission_classes = [IsAuthenticated, IsDeliveryUser]
    
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
                'message': 'Pedido no encontrado o no asignado a ti'
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
                'can_mark_paid': not order.is_paid and order.status != 'entregado',
                'can_report_incidence': order.status not in ['entregado', 'cancelado'],
                'can_cancel': order.status not in ['entregado', 'cancelado'],
            }
        })


class DeliveryMarkAsPaidAPIView(APIView):
    """
    HU-034: Marcar pedido como pagado
    POST /api/delivery/orders/<int:order_id>/mark-paid/
    """
    permission_classes = [IsAuthenticated, IsDeliveryUser]
    
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
                'message': 'Pedido no encontrado o no asignado a ti'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar que el pedido no esté ya pagado
        if order.is_paid:
            return Response({
                'success': False,
                'message': 'Este pedido ya fue marcado como pagado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que el pedido esté en camino
        if order.status != 'en_camino':
            return Response({
                'success': False,
                'message': f'Solo se puede marcar como pagado pedidos "En camino". Estado actual: {order.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar datos
        serializer = MarkAsPaidSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Marcar como pagado
        try:
            order.is_paid = True
            order.save(update_fields=['is_paid', 'updated_at'])
            order.updated_by = user
            order.save(update_fields=['updated_by'])
            
            logger.info(f"Pedido {order.order_number} marcado como pagado por {user.username}")
            
            return Response({
                'success': True,
                'message': f'Pedido {order.order_number} marcado como pagado',
                'order_id': order.id,
                'order_number': order.order_number,
                'paid_at': timezone.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"Error al marcar pedido {order.id} como pagado: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error al procesar el pago'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeliveryIncidenceAPIView(APIView):
    """
    HU-035: Registrar incidencia en un pedido
    POST /api/delivery/incidences/
    """
    permission_classes = [IsAuthenticated, IsDeliveryUser]
    
    def post(self, request):
        user = request.user
        order_id = request.data.get('order_id')
        
        if not order_id:
            return Response({
                'success': False,
                'message': 'Se requiere order_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(
                id=order_id,
                assigned_delivery_user=user
            )
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Pedido no encontrado o no asignado a ti'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar que el pedido no esté entregado o cancelado
        if order.status in ['entregado', 'cancelado']:
            return Response({
                'success': False,
                'message': f'No se puede reportar incidencia en pedido con estado: {order.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar datos
        serializer = IncidenceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        incidence_type = data['incidence_type']
        comments = data.get('comments', '')
        action = data.get('action', 'report')
        
        # Construir objeto incidencia
        incidence_data = {
            'type': incidence_type,
            'type_label': dict(serializer.fields['incidence_type'].choices).get(incidence_type, ''),
            'comments': comments,
            'reported_by': user.id,
            'reported_by_name': user.get_full_name() or user.username,
            'reported_at': timezone.now().isoformat(),
            'action_taken': action,
        }
        
        try:
            if action == 'cancel':
                # Cancelar el pedido
                reason = json.dumps(incidence_data, ensure_ascii=False)
                order.cancel(reason, user=user)
                logger.info(f"Pedido {order.order_number} cancelado por incidencia: {incidence_type}")
                
                return Response({
                    'success': True,
                    'message': f'Pedido {order.order_number} cancelado por: {incidence_data["type_label"]}',
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'status': 'cancelado',
                    'incidence': incidence_data,
                })
            else:
                # Solo reportar incidencia (guardar en cancelled_reason como JSON)
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
                
                logger.info(f"Incidencia {incidence_type} reportada en pedido {order.order_number}")
                
                return Response({
                    'success': True,
                    'message': f'Incidencia reportada: {incidence_data["type_label"]}',
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'status': order.status,
                    'incidence': incidence_data,
                })
                
        except Exception as e:
            logger.error(f"Error al reportar incidencia en pedido {order.id}: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error al procesar la incidencia: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeliverySummaryAPIView(APIView):
    """
    HU-036: Resumen del día del entregador
    GET /api/delivery/summary/
    """
    permission_classes = [IsAuthenticated, IsDeliveryUser]
    
    def get(self, request):
        user = request.user
        today = date.today()
        
        # Pedidos del día
        orders = Order.objects.filter(
            assigned_delivery_user=user,
            created_at__date=today
        )
        
        delivered_orders = orders.filter(status='entregado')
        total_delivered = delivered_orders.count()
        total_paid = delivered_orders.filter(is_paid=True).count()
        total_amount = delivered_orders.aggregate(total=models.Sum('total_amount'))['total'] or 0
        
        pending_payment = orders.filter(is_paid=False, status__in=['listo', 'en_camino']).count()
        pending_amount = orders.filter(is_paid=False, status__in=['listo', 'en_camino']).aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0
        
        # Incidencias del día
        incidences = []
        for order in orders.filter(cancelled_reason__isnull=False).exclude(cancelled_reason=''):
            try:
                data = json.loads(order.cancelled_reason)
                if isinstance(data, list):
                    for inc in data:
                        incidences.append({
                            'order_id': order.id,
                            'order_number': order.order_number,
                            'type': inc.get('type_label', 'Desconocida'),
                            'comments': inc.get('comments', ''),
                            'reported_at': inc.get('reported_at', order.updated_at.isoformat()),
                        })
                elif isinstance(data, dict):
                    incidences.append({
                        'order_id': order.id,
                        'order_number': order.order_number,
                        'type': data.get('type_label', 'Desconocida'),
                        'comments': data.get('comments', ''),
                        'reported_at': data.get('reported_at', order.updated_at.isoformat()),
                    })
            except json.JSONDecodeError:
                continue
        
        summary = {
            'date': today.isoformat(),
            'total_delivered': total_delivered,
            'total_paid': total_paid,
            'total_amount': total_amount,
            'pending_payment': pending_payment,
            'pending_amount': pending_amount,
            'delivered_orders': [
                {
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer': order.customer_name,
                    'amount': order.total_amount,
                    'paid': order.is_paid,
                }
                for order in delivered_orders
            ],
            'incidences': incidences,
        }
        
        return Response({
            'success': True,
            'summary': summary,
        })