from .base import BaseReport
from .querys import (
    get_delivery_stats_in_range,
    get_delivery_performance_in_range,
    get_daily_deliveries_in_range,
    get_delivery_summary_stats,
    get_delivery_details_list,
)


class DeliveryReport(BaseReport):
    def get_title(self):
        return "Reporte de Entregadores"

    def get_template(self):
        return "backoffice/reports/delivery_report.html"

    def get_data(self):
        start = self.params['date_from']
        end = self.params['date_to']
        include_charts = self.params.get('include_charts', False)
        include_tables = self.params.get('include_tables', True)

        # ========== ESTADÍSTICAS GENERALES ==========
        delivery_stats = get_delivery_stats_in_range(start, end)
        
        # ========== RESUMEN DE ENTREGAS ==========
        summary_stats = get_delivery_summary_stats(start, end)
        
        # ========== RENDIMIENTO POR ENTREGADOR ==========
        top_deliveries = get_delivery_performance_in_range(start, end, limit=10)
        
        # ========== ENTREGAS DIARIAS ==========
        daily_categories, daily_counts, daily_revenues = get_daily_deliveries_in_range(start, end)
        
        # Combinar datos diarios
        daily_combined = []
        for i in range(len(daily_categories)):
            daily_combined.append({
                'date': daily_categories[i],
                'deliveries': daily_counts[i],
                'revenue': daily_revenues[i],
            })

        # ========== LISTA DETALLADA ==========
        delivery_details = get_delivery_details_list(start, end, limit=20)

        return {
            # Estadísticas de entregadores
            'total_deliveries_users': delivery_stats['total_deliveries'],
            'active_deliveries': delivery_stats['active_deliveries'],
            'inactive_deliveries': delivery_stats['inactive_deliveries'],
            'deliveries_with_activity': delivery_stats['deliveries_with_activity'],
            'inactive_deliveries_no_activity': delivery_stats['inactive_deliveries_no_activity'],
            
            # Resumen de entregas
            'total_deliveries': summary_stats['total_deliveries'],
            'total_revenue': f"${summary_stats['total_revenue']:,.0f}",
            'unique_deliveries': summary_stats['unique_deliveries'],
            'avg_revenue_per_delivery': f"${summary_stats['avg_revenue_per_delivery']:,.0f}",
            'avg_deliveries_per_day': summary_stats['avg_deliveries_per_day'],
            'best_day': summary_stats['best_day'],
            'best_day_count': summary_stats['best_day_count'],
            
            # Top entregadores
            'top_deliveries': top_deliveries,
            
            # Datos diarios
            'daily_combined': daily_combined,
            
            # Lista detallada
            'delivery_details': delivery_details,
            
            # Flags
            'include_charts': include_charts,
            'include_tables': include_tables,
        }