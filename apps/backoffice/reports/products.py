from .base import BaseReport
from .queries import (
    get_product_stats_in_range,
    get_category_stats_in_range,
    get_top_selling_products_in_range,
    get_low_stock_variants_in_range,
    get_out_of_stock_variants_in_range,
    get_products_without_sales_in_range,
    get_stock_movement_summary,
)


class ProductsReport(BaseReport):
    def get_title(self):
        return "Reporte de Productos"

    def get_template(self):
        return "backoffice/reports/products_report.html"

    def get_data(self):
        start = self.params['date_from']
        end = self.params['date_to']
        include_charts = self.params.get('include_charts', False)
        include_tables = self.params.get('include_tables', True)

        # ========== ESTADÍSTICAS GENERALES ==========
        product_stats = get_product_stats_in_range(start, end)
        
        # ========== MOVIMIENTO DE STOCK ==========
        stock_movement = get_stock_movement_summary(start, end)
        
        # ========== TOP PRODUCTOS ==========
        top_products = get_top_selling_products_in_range(start, end, limit=10)
        
        # ========== VENTAS POR CATEGORÍA ==========
        category_stats = get_category_stats_in_range(start, end)
        
        # ========== STOCK PROBLEMÁTICO ==========
        low_stock_variants = get_low_stock_variants_in_range(limit=15)
        out_of_stock_variants = get_out_of_stock_variants_in_range(limit=15)
        products_without_sales = get_products_without_sales_in_range(start, end, limit=15)

        return {
            # Estadísticas generales
            'total_products': product_stats['total_products'],
            'total_variants': product_stats['total_variants'],
            'variants_with_stock': product_stats['variants_with_stock'],
            'variants_low_stock': product_stats['variants_low_stock'],
            'variants_out_stock': product_stats['variants_out_stock'],
            'products_with_sales': product_stats['products_with_sales'],
            'products_without_sales_count': product_stats['products_without_sales'],
            
            # Movimiento de stock
            'units_sold': stock_movement['units_sold'],
            'stock_revenue': f"${stock_movement['revenue']:,.0f}",
            'avg_price_per_unit': f"${stock_movement['avg_price_per_unit']:,.0f}",
            
            # Top productos
            'top_products': top_products,
            
            # Ventas por categoría
            'category_stats': category_stats,
            
            # Stock problemático
            'low_stock_variants': low_stock_variants,
            'out_of_stock_variants': out_of_stock_variants,
            'products_without_sales_list': products_without_sales,

            # Flags
            'include_charts': include_charts,
            'include_tables': include_tables,
        }