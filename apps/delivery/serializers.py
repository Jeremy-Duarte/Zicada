from rest_framework import serializers
from apps.orders.models import Order, OrderItem
from django.contrib.auth import get_user_model

User = get_user_model()


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer para items de pedido"""
    product_name = serializers.CharField(source='product_name_snapshot')
    size = serializers.CharField(source='size_snapshot')
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_name', 'size', 'quantity', 
            'unit_price', 'subtotal', 'stock_snapshot'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer para lista de pedidos (HU-033)"""
    customer_name = serializers.CharField()
    customer_phone = serializers.CharField()
    shipping_address = serializers.CharField(allow_blank=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_paid = serializers.BooleanField()
    status_display = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_phone',
            'shipping_address', 'total_amount', 'is_paid', 'status',
            'status_display', 'status_color', 'delivery_notes',
            'created_at', 'updated_at'
        ]
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_status_color(self, obj):
        """Retorna color según estado para UI"""
        colors = {
            'pendiente': 'gray',
            'confirmado': 'blue',
            'preparando': 'yellow',
            'listo': 'green',
            'en_camino': 'purple',
            'entregado': 'green',
            'cancelado': 'red',
        }
        return colors.get(obj.status, 'gray')


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle de pedido (HU-034, HU-035)"""
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField()
    customer_phone = serializers.CharField()
    customer_email = serializers.EmailField(allow_null=True, allow_blank=True)
    shipping_address = serializers.CharField(allow_blank=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_paid = serializers.BooleanField()
    status_display = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()
    assigned_delivery_user = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_phone',
            'customer_email', 'shipping_address', 'delivery_notes',
            'subtotal', 'shipping_cost', 'total_amount', 'is_paid',
            'status', 'status_display', 'status_color', 'cancelled_reason',
            'assigned_delivery_user', 'created_at', 'updated_at', 'items'
        ]
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_status_color(self, obj):
        colors = {
            'pendiente': 'gray',
            'confirmado': 'blue',
            'preparando': 'yellow',
            'listo': 'green',
            'en_camino': 'purple',
            'entregado': 'green',
            'cancelado': 'red',
        }
        return colors.get(obj.status, 'gray')
    
    def get_assigned_delivery_user(self, obj):
        if obj.assigned_delivery_user:
            return {
                'id': obj.assigned_delivery_user.id,
                'name': obj.assigned_delivery_user.get_full_name() or obj.assigned_delivery_user.username,
                'phone': getattr(obj.assigned_delivery_user, 'phone', None)
            }
        return None


class OrderSummarySerializer(serializers.Serializer):
    """Serializer para resumen del día (HU-036)"""
    date = serializers.DateField()
    total_delivered = serializers.IntegerField()
    total_paid = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_payment = serializers.IntegerField()
    pending_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    delivered_orders = serializers.ListField(child=serializers.DictField())
    incidences = serializers.ListField(child=serializers.DictField())


class MarkAsPaidSerializer(serializers.Serializer):
    """Serializer para marcar como pagado (HU-034)"""
    confirm = serializers.BooleanField(required=True)
    payment_method = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class IncidenceSerializer(serializers.Serializer):
    """Serializer para reportar incidencia (HU-035)"""
    incidence_type = serializers.ChoiceField(choices=[
        ('customer_not_home', 'Cliente no estaba'),
        ('wrong_address', 'Dirección incorrecta'),
        ('customer_cancelled', 'Cliente canceló'),
        ('product_rejected', 'Producto rechazado'),
        ('other', 'Otro'),
    ])
    comments = serializers.CharField(required=False, allow_blank=True)
    action = serializers.ChoiceField(choices=['report', 'cancel'], default='report')