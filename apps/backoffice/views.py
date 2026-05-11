from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from apps.orders.models import Order, OrderItem
from apps.products.models import ProductVariant
from apps.users.models import User
from django.db.models import Sum

from django.db.models import Sum
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from apps.orders.models import Order, OrderItem
from apps.products.models import ProductVariant
from apps.users.models import User

@staff_member_required
def admin_dashboard(request):
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    PAID_STATUSES = ['confirmado', 'preparando', 'listo', 'en_camino', 'entregado']

    # ========== ESTADÍSTICAS BÁSICAS ==========
    pending_orders = Order.objects.filter(status='pendiente').count()

    today_orders = Order.objects.filter(created_at__date=today).count()

    # Ingresos del mes (confirmados o posteriores)
    month_revenue = Order.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month,
        status__in=PAID_STATUSES
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    active_deliveries = User.objects.filter(is_delivery=True, is_active=True).count()

    # ========== MÉTRICAS FINANCIERAS ==========

    # Ingreso diario (hoy) - incluye confirmado en adelante
    today_revenue = Order.objects.filter(
        created_at__date=today,
        status__in=PAID_STATUSES
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Ingreso semanal (últimos 7 días)
    week_ago = today - timedelta(days=7)
    week_revenue = Order.objects.filter(
        created_at__date__gte=week_ago,
        created_at__date__lte=today,
        status__in=PAID_STATUSES
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Ingreso anual
    year_revenue = Order.objects.filter(
        created_at__year=current_year,
        status__in=PAID_STATUSES
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Promedio por pedido (basado en pedidos confirmados o posteriores)
    total_paid_orders = Order.objects.filter(status__in=PAID_STATUSES).count()
    avg_order_value = (month_revenue / total_paid_orders) if total_paid_orders > 0 else 0

    # Ticket promedio (por item) sobre pedidos pagados
    total_items_sold = OrderItem.objects.filter(
        order__status__in=PAID_STATUSES
    ).aggregate(total=Sum('quantity'))['total'] or 0
    avg_items_per_order = total_items_sold / total_paid_orders if total_paid_orders > 0 else 0

    # ========== GRÁFICO DE VENTAS (últimos 7 días) ==========
    sales_data = []
    categories = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        categories.append(date.strftime('%d/%m'))
        daily_total = Order.objects.filter(
            created_at__date=date,
            status__in=PAID_STATUSES
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        sales_data.append(float(daily_total))

    # Si no hay datos, dejar ceros
    if sum(sales_data) == 0:
        sales_data = [0, 0, 0, 0, 0, 0, 0]

    # ========== GRÁFICO DE INGRESO DIARIO (últimos 7 días) ==========
    daily_revenue_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        daily_total = Order.objects.filter(
            created_at__date=date,
            status__in=PAID_STATUSES
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        daily_revenue_data.append(float(daily_total))

    # ========== GRÁFICO DE ESTADO DE PEDIDOS ==========
    status_labels = {
        'pendiente': 'Pendientes',
        'confirmado': 'Confirmados',
        'preparando': 'Preparando',
        'listo': 'Listos',
        'en_camino': 'En camino',
        'entregado': 'Entregados',
        'cancelado': 'Cancelados',
    }
    status_counts = []
    status_names = []
    for status_code in ['pendiente', 'confirmado', 'preparando', 'listo', 'en_camino', 'entregado', 'cancelado']:
        count = Order.objects.filter(status=status_code).count()
        if count > 0:
            status_counts.append(count)
            status_names.append(status_labels.get(status_code, status_code))

    # ========== PEDIDOS RECIENTES ==========
    recent_orders_qs = Order.objects.select_related('assigned_delivery_user').order_by('-created_at')[:5]
    recent_orders = []
    for order in recent_orders_qs:
        recent_orders.append({
            'title': f"Pedido {order.order_number}",
            'subtitle': order.customer_name,
            'value': f"${order.total_amount:,.0f}",
            'date': order.created_at.strftime('%d/%m %H:%M'),
            'icon': 'box',
            'icon_bg': 'gray-100',
            'icon_color': 'zicada-accent',
        })

    # ========== PRODUCTOS CON STOCK BAJO ==========
    low_stock_variants = ProductVariant.objects.filter(
        is_active=True,
        stock__gt=0,
        stock__lte=10
    ).select_related('product', 'size', 'product_color__color')[:5]
    low_stock_products = []
    for variant in low_stock_variants:
        low_stock_products.append({
            'title': variant.product.name,
            'subtitle': f"{variant.size.name} - {variant.color_name}",
            'value': f"{variant.stock} unidades",
            'icon': 'exclamation-triangle',
            'icon_bg': 'yellow-100',
            'icon_color': 'yellow-600',
        })

    # ========== TOP PRODUCTOS MÁS VENDIDOS ==========
    top_products = OrderItem.objects.filter(
        order__status__in=PAID_STATUSES
    ).values('product_name_snapshot').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_quantity')[:5]
    top_products_list = []
    for product in top_products:
        top_products_list.append({
            'title': product['product_name_snapshot'],
            'subtitle': f"{product['total_quantity']} unidades vendidas",
            'value': f"${product['total_revenue']:,.0f}",
            'icon': 'chart-line',
            'icon_bg': 'green-100',
            'icon_color': 'green-600',
        })

    # Datos para gráficos
    sales_chart_data = {
        'series': [{'name': 'Ventas (COP)', 'data': sales_data}],
        'categories': categories,
    }
    daily_revenue_chart_data = {
        'series': [{'name': 'Ingreso diario (COP)', 'data': daily_revenue_data}],
        'categories': categories,
    }
    orders_status_data = {
        'series': status_counts,
        'labels': status_names,
    }

    context = {
        'section': 'dashboard',
        'stats': {
            'pending_orders': pending_orders,
            'today_orders': today_orders,
            'month_revenue': f"${month_revenue:,.0f}",
            'active_deliveries': active_deliveries,
        },
        'financial_stats': {
            'today_revenue': f"${today_revenue:,.0f}",
            'week_revenue': f"${week_revenue:,.0f}",
            'month_revenue': f"${month_revenue:,.0f}",
            'year_revenue': f"${year_revenue:,.0f}",
            'avg_order_value': f"${avg_order_value:,.0f}",
            'avg_items_per_order': f"{avg_items_per_order:.1f}",
        },
        'sales_chart_data': sales_chart_data,
        'daily_revenue_chart_data': daily_revenue_chart_data,
        'orders_status_data': orders_status_data,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'top_products': top_products_list,
    }
    return render(request, 'backoffice/admin_dashboard.html', context)

@staff_member_required
def admin_orders(request):
    context = {'section': 'orders'}
    return render(request, 'backoffice/admin_orders.html', context)

@staff_member_required
def admin_products(request):
    context = {'section': 'products'}
    return render(request, 'backoffice/admin_products.html', context)

@staff_member_required
def admin_users(request):
    context = {'section': 'users'}
    return render(request, 'backoffice/admin_users.html', context)

@staff_member_required
def admin_config(request):
    context = {'section': 'config'}
    return render(request, 'backoffice/admin_config.html', context)