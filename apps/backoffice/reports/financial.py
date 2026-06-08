from .base import BaseReport
from .querys import (
    sum_order_amount_in_range,
    get_daily_data_in_range,
    get_daily_order_counts_in_range,
    get_status_chart_data_in_range,
    get_top_products_in_range,
)
from apps.orders.models import Order


class FinancialReport(BaseReport):
    def get_title(self):
        return "Reporte Financiero"

    def get_template(self):
        return "backoffice/reports/financial_report.html"

    def get_data(self):
        start = self.params['date_from']
        end = self.params['date_to']
        include_charts = self.params.get('include_charts', False)
        include_tables = self.params.get('include_tables', True)

        # ========== MÉTRICAS PRINCIPALES ==========
        revenue = sum_order_amount_in_range(start, end)
        orders_count = Order.objects.filter(
            created_at__date__gte=start,
            created_at__date__lte=end
        ).count()
        
        paid_statuses = ['confirmado', 'preparando', 'listo', 'en_camino', 'entregado']
        paid_orders = Order.objects.filter(
            created_at__date__gte=start,
            created_at__date__lte=end,
            status__in=paid_statuses
        ).count()
        
        avg_order = revenue / paid_orders if paid_orders else 0

        # ========== DATOS DIARIOS ==========
        daily_categories, daily_revenue = get_daily_data_in_range(start, end)
        _ , daily_orders_counts = get_daily_order_counts_in_range(start, end)

        # ========== COMBINAR DATOS DIARIOS ==========
        daily_combined = []
        for i in range(len(daily_categories)):
            daily_combined.append({
                'date': daily_categories[i],
                'revenue': daily_revenue[i],
                'orders': daily_orders_counts[i],
            })

        # ========== TOP PRODUCTOS ==========
        top_products = get_top_products_in_range(start, end, limit=10)

        # ========== DISTRIBUCIÓN DE ESTADOS ==========
        status_data = get_status_chart_data_in_range(start, end)

        # ========== COMBINAR DATOS DE ESTADOS ==========
        status_combined = []
        for label, count in zip(status_data['labels'], status_data['series']):
            status_combined.append({'label': label, 'count': count})

        return {
            'revenue': f"${revenue:,.0f}",
            'orders_count': orders_count,
            'paid_orders': paid_orders,
            'avg_order': f"${avg_order:,.0f}",
            
            'daily_combined': daily_combined,
            'status_combined': status_combined,
            'top_products': top_products,
            
            'include_charts': include_charts,
            'include_tables': include_tables,
        }