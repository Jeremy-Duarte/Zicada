from .base import BaseReport
from .queries import (
    get_order_stats_summary,
    get_daily_order_counts_in_range,
    get_daily_revenue_in_range,
    get_top_customers_in_range,
    get_order_status_distribution_in_range,
    get_avg_items_per_order_in_range,
)


class OrdersReport(BaseReport):
    def get_title(self):
        return "Reporte de Pedidos"

    def get_template(self):
        return "backoffice/reports/orders_report.html"

    def get_data(self):
        start = self.params['date_from']
        end = self.params['date_to']
        include_charts = self.params.get('include_charts', False)
        include_tables = self.params.get('include_tables', True)

        # ========== MÉTRICAS PRINCIPALES ==========
        stats = get_order_stats_summary(start, end)
        
        # ========== ITEMS POR PEDIDO ==========
        avg_items = get_avg_items_per_order_in_range(start, end)

        # ========== DATOS DIARIOS ==========
        daily_categories, daily_counts = get_daily_order_counts_in_range(start, end)
        _ , daily_revenues = get_daily_revenue_in_range(start, end)
        
        # Combinar datos diarios
        daily_combined = []
        for i in range(len(daily_categories)):
            daily_combined.append({
                'date': daily_categories[i],
                'orders': daily_counts[i],
                'revenue': daily_revenues[i] if i < len(daily_revenues) else 0,
            })

        # ========== DISTRIBUCIÓN POR ESTADO ==========
        status_distribution = get_order_status_distribution_in_range(start, end)

        # ========== TOP CLIENTES ==========
        top_customers = get_top_customers_in_range(start, end, limit=10)

        return {
            # Métricas principales
            'total_orders': stats['total_orders'],
            'paid_orders': stats['paid_orders'],
            'cancelled_orders': stats['cancelled_orders'],
            'revenue': f"${stats['revenue']:,.0f}",
            'avg_order_value': f"${stats['avg_order_value']:,.0f}",
            'avg_items_per_order': f"{avg_items:.1f}",
            
            # Datos combinados
            'daily_combined': daily_combined,
            'status_distribution': status_distribution,
            'top_customers': top_customers,
            
            # Flags
            'include_charts': include_charts,
            'include_tables': include_tables,
        }