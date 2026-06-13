import re
import json
import csv
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Min, Max, Count
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.core.management import call_command
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.views import View
from apps.core.crud.mixins import StaffPermissionRequiredMixin
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.http import HttpResponse

from apps.core.crud.mixins import PaginationMixin, FilterMixin, SortableDeleteMixin
from .models import Product, ProductVariant, ProductColor, ProductImage, Collection, Category, Size, Color
from .forms import (
    SizeCreateForm, SizeDeleteForm, SizeUpdateForm,
    CategoryCreateForm, CategoryDeleteForm, CategoryUpdateForm,
    ColorCreateForm, ColorDeleteForm, ColorUpdateForm, ColorImportForm,
    ProductImageCreateForm, ProductImageUpdateForm, ProductImageDeleteForm,
    ProductUpdateForm, ProductDeleteForm, ProductCreateForm, ProductRestoreForm,
    ProductColorCreateForm, ProductColorUpdateForm, ProductColorDeleteForm,
    ProductVariantCreateForm, ProductVariantDeleteForm, ProductVariantRestoreForm, ProductVariantUpdateForm,
    CollectionCreateForm, CollectionUpdateForm, CollectionDeleteForm, CollectionRestoreForm, CollectionStyleForm
)
from apps.products.importers.size_importer import SizeImporter
from apps.products.importers.color_importer import ColorImporter
from apps.products.importers.category_importer import CategoryImporter

from apps.core.url_names import (
    PRODUCTS_SIZE_LIST,
    PRODUCTS_SIZE_IMPORT,
    PRODUCTS_CATEGORY_LIST,
    PRODUCTS_CATEGORY_IMPORT,
    PRODUCTS_COLOR_LIST,
    PRODUCTS_COLOR_IMPORT,
    PRODUCTS_IMAGE_LIST,
    PRODUCTS_LIST,
    PRODUCTS_EDIT,
    PRODUCTS_TRASHCAN,
    PRODUCTS_COLLECTION_LIST,
    PRODUCTS_COLLECTION_CREATE,
    PRODUCTS_COLLECTION_EDIT,
    PRODUCTS_COLLECTION_DELETE,
    PRODUCTS_COLLECTION_RESTORE,
    PRODUCTS_COLLECTION_TRASHCAN,
    PRODUCTS_COLLECTION_STYLE,
)

from .constants import (
    # Umbral de bajo stock
    STOCK_LOW_THRESHOLD,
    # Status Strings
    STATUS_PUBLISHED,
    STATUS_DRAFT,
    STATUS_ARCHIVED,
    # Status Filter Choices
    STATUS_FILTER_ACTIVE,
    STATUS_FILTER_UPCOMING,
    STATUS_FILTER_ARCHIVED,
    STATUS_FILTER_CHOICES,
    # Active/Inactive Filter Values
    ACTIVE_FILTER_VALUE,
    INACTIVE_FILTER_VALUE,
    # Collection Filters
    COLLECTION_FILTER_STATUS,
    COLLECTION_ORDER,
    # Product Filters
    PRODUCT_FILTER_ACTIVE,
    PRODUCT_LIMIT_RELATED,
    # Stock Thresholds
    STOCK_ZERO,
    # Order By
    ORDER_BY_CREATED_AT,
    ORDER_BY_SORT_ORDER,
    ORDER_BY_DELETED_AT,
    # Order Choices
    ORDER_CHOICE_RECENT,
    ORDER_CHOICE_OLDEST,
    ORDER_CHOICE_NAME_ASC,
    ORDER_CHOICE_NAME_DESC,
    ORDER_CHOICE_PRICE_DESC,
    ORDER_CHOICE_PRICE_ASC,
    ORDER_CHOICE_START_DATE_DESC,
    ORDER_CHOICE_START_DATE_ASC,
    ORDER_CHOICES_CATALOG,
    ORDER_CHOICES_COLLECTIONS,
    # Pagination
    PAGINATE_BY_DEFAULT,
    PAGINATE_BY_COLLECTIONS,
    # Date Formats
    DATE_FORMAT_DISPLAY,
    DATE_FORMAT_DAY_MONTH_YEAR,
    # Template Paths
    TEMPLATE_STOCK_DASHBOARD,
    TEMPLATE_CATALOG,
    TEMPLATE_COLLECTIONS_LIST_PUBLIC,
    TEMPLATE_COLLECTION_DETAIL,
    TEMPLATE_PRODUCT_DETAIL,
    # Backoffice Templates
    TEMPLATE_SIZE_LIST,
    TEMPLATE_SIZE_FORM,
    TEMPLATE_SIZE_CONFIRM_DELETE,
    TEMPLATE_SIZE_IMPORT,
    TEMPLATE_SIZE_IMPORT_RESULT,
    TEMPLATE_CATEGORY_LIST,
    TEMPLATE_CATEGORY_FORM,
    TEMPLATE_CATEGORY_CONFIRM_DELETE,
    TEMPLATE_CATEGORY_IMPORT,
    TEMPLATE_CATEGORY_IMPORT_RESULT,
    TEMPLATE_COLOR_LIST,
    TEMPLATE_COLOR_FORM,
    TEMPLATE_COLOR_CONFIRM_DELETE,
    TEMPLATE_COLOR_IMPORT,
    TEMPLATE_COLOR_IMPORT_RESULT,
    TEMPLATE_PRODUCTIMAGE_LIST,
    TEMPLATE_PRODUCTIMAGE_FORM,
    TEMPLATE_PRODUCTIMAGE_CONFIRM_DELETE,
    TEMPLATE_PRODUCT_LIST,
    TEMPLATE_PRODUCT_FORM,
    TEMPLATE_PRODUCT_CONFIRM_DELETE,
    TEMPLATE_PRODUCT_RESTORE,
    TEMPLATE_PRODUCT_TRASHCAN,
    TEMPLATE_PRODUCTCOLOR_FORM,
    TEMPLATE_PRODUCTCOLOR_CONFIRM_DELETE,
    TEMPLATE_PRODUCTVARIANT_FORM,
    TEMPLATE_PRODUCTVARIANT_CONFIRM_DELETE,
    TEMPLATE_PRODUCTVARIANT_RESTORE,
    TEMPLATE_PRODUCTVARIANT_TRASHCAN,
    TEMPLATE_COLLECTIONS_LIST, 
    TEMPLATE_COLLECTION_FORM,
    TEMPLATE_COLLECTION_CONFIRM_DELETE,
    TEMPLATE_COLLECTION_RESTORE,
    TEMPLATE_COLLECTION_TRASHCAN,
    TEMPLATE_COLLECTION_STYLE_FORM,
    # Form Context Keys
    CONTEXT_CANCEL_URL,
    CONTEXT_CANCEL_ARGS,
    CONTEXT_TITLE,
    CONTEXT_IS_CREATE,
    CONTEXT_IS_UPDATE,
    CONTEXT_OBJECT_NAME,
    CONTEXT_OBJECT_DISPLAY,
    CONTEXT_IMAGE_PREVIEW,
    CONTEXT_PRODUCT,
    CONTEXT_PRODUCTS,
    CONTEXT_PRODUCT_COLORS,
    CONTEXT_VARIANTS,
    # Table Headers
    HEADER_NAME,
    HEADER_SLUG,
    HEADER_ORDER,
    HEADER_CODE,
    HEADER_IMAGE,
    HEADER_ALT_TEXT,
    HEADER_UPLOADED,
    HEADER_CATEGORY,
    HEADER_PRICE,
    HEADER_TYPE,
    HEADER_STATUS,
    HEADER_DELETED_AT,
    HEADER_COVER_IMAGE,
    HEADER_PRODUCT_COUNT,
    HEADER_PRICE_RANGE,
    HEADER_DATES,
    # Table Header Lists
    HEADERS_SIZE,
    HEADERS_CATEGORY,
    HEADERS_COLOR,
    HEADERS_PRODUCT_IMAGE,
    HEADERS_PRODUCT,
    HEADERS_PRODUCT_TRASHCAN,
    HEADERS_COLLECTION,
    # Product Types
    PRODUCT_TYPE_FABRICA,
    PRODUCT_TYPE_COLECCION_LIMITADA,
    PRODUCT_TYPES_DISPLAY,
    # Stock Display Messages
    STOCK_MESSAGE_OUT_OF_STOCK,
    STOCK_MESSAGE_LOW_STOCK,
    STOCK_MESSAGE_AVAILABLE,
    # Stock Display Classes
    STOCK_CLASS_OUT_OF_STOCK,
    STOCK_CLASS_LOW_STOCK,
    STOCK_CLASS_AVAILABLE,
    # Status Badge Classes
    BADGE_CLASS_ACTIVE,
    BADGE_CLASS_INACTIVE,
    BADGE_TEXT_ACTIVE,
    BADGE_TEXT_INACTIVE,
    # Filter Configuration
    FILTER_CONFIG_DEFAULT,
    FILTER_CONFIG_WITH_STATUS,
    # Filter Labels
    FILTER_LABEL_STATUS,
    FILTER_LABEL_CATEGORY,
    FILTER_LABEL_TYPE,
    FILTER_LABEL_PRICE,
    # Filter Names
    FILTER_NAME,
    FILTER_CATEGORY,
    FILTER_PRODUCT_TYPE,
    FILTER_IS_ACTIVE,
    # Query Parameters
    QUERY_PARAM_CATEGORY,
    QUERY_PARAM_SEARCH,
    QUERY_PARAM_STATUS,
    QUERY_PARAM_MIN_PRICE,
    QUERY_PARAM_MAX_PRICE,
    QUERY_PARAM_PRODUCT_COUNT_MIN,
    QUERY_PARAM_PRODUCT_COUNT_MAX,
    QUERY_PARAM_DATE_FILTER,
    QUERY_PARAM_PRODUCT_TYPE,
    QUERY_PARAM_ORDER_BY,
    # Date Filter Options
    DATE_FILTER_LAST_MONTH,
    DATE_FILTER_LAST_QUARTER,
    DATE_FILTER_LAST_SEMESTER,
    DATE_FILTER_LAST_YEAR,
    DATE_FILTER_UPCOMING,
    # Import Form Field Names
    IMPORT_FILE_FIELD,
    IMPORT_UPDATE_EXISTING_FIELD,
    # Import Template Columns
    IMPORT_TEMPLATE_COLUMNS_SIZE,
    IMPORT_TEMPLATE_COLUMNS_COLOR,
    IMPORT_TEMPLATE_COLUMNS_CATEGORY,
    # Import Messages
    MSG_IMPORT_NO_FILE,
    # UI Text Strings
    UI_NO_IMAGE,
    UI_STATUS_LABEL,
    UI_PLACEHOLDER_SEARCH_PRODUCT,
    # Icon HTML
    ICON_IMAGE_PLACEHOLDER,
    # Success Messages
    MSG_SIZE_CREATED,
    MSG_SIZE_UPDATED,
    MSG_SIZE_DELETED,
    MSG_CATEGORY_CREATED,
    MSG_CATEGORY_UPDATED,
    MSG_CATEGORY_DELETED,
    MSG_COLOR_CREATED,
    MSG_COLOR_UPDATED,
    MSG_COLOR_DELETED,
    MSG_PRODUCT_IMAGE_UPLOADED,
    MSG_PRODUCT_IMAGE_UPDATED,
    MSG_PRODUCT_IMAGE_DELETED,
    MSG_PRODUCT_CREATED,
    MSG_PRODUCT_UPDATED,
    MSG_PRODUCT_DELETED,
    MSG_PRODUCT_RESTORED,
    MSG_PRODUCT_COLOR_UPDATED,
    MSG_PRODUCT_COLOR_DELETED,
    MSG_VARIANT_CREATED,
    MSG_VARIANT_UPDATED,
    MSG_VARIANT_DELETED,
    MSG_VARIANT_RESTORED,
    MSG_VARIANT_RESTORE_ERROR,
    MSG_COLLECTION_CREATED,
    MSG_COLLECTION_UPDATED,
    MSG_COLLECTION_DELETED,
    MSG_COLLECTION_RESTORED,
    MSG_COLLECTION_STYLE_UPDATED,
    # Import Template Filenames
    IMPORT_TEMPLATE_FILENAME_SIZE,
    IMPORT_TEMPLATE_FILENAME_COLOR,
    IMPORT_TEMPLATE_FILENAME_CATEGORY,
    # Import Example Data
    IMPORT_EXAMPLE_DATA_SIZE,
    IMPORT_EXAMPLE_DATA_COLOR,
    IMPORT_EXAMPLE_DATA_CATEGORY,
    # Perms
    PERM_COLLECTION_VIEW,
    PERM_COLLECTION_ADD,
    PERM_COLLECTION_CHANGE,
    PERM_COLLECTION_DELETE,
)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_stock_display(stock: int) -> tuple:
    """Get stock display type and message based on stock quantity."""
    if stock == STOCK_ZERO:
        return STOCK_CLASS_OUT_OF_STOCK, STOCK_MESSAGE_OUT_OF_STOCK
    elif stock <= STOCK_LOW_THRESHOLD:
        return STOCK_CLASS_LOW_STOCK, STOCK_MESSAGE_LOW_STOCK.format(stock=stock)
    else:
        return STOCK_CLASS_AVAILABLE, STOCK_MESSAGE_AVAILABLE


def generate_csv_response(filename: str, headers: list, rows: list) -> HttpResponse:
    """Generate CSV response for template download."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    
    return response


# =============================================================================
# PUBLIC VIEWS
# =============================================================================

@staff_member_required
@require_GET
def stock_dashboard(request):
    """Stock dashboard for staff members."""
    low_stock_variants = ProductVariant.objects.low_stock().select_related('product', 'product_color__color', 'size')
    out_of_stock_variants = ProductVariant.objects.out_of_stock().select_related('product', 'product_color__color', 'size')
    
    products_with_stock = Product.objects.filter(
        variants__is_active=True,
        variants__stock__gt=STOCK_ZERO
    ).distinct()
    
    all_products = Product.objects.filter(is_active=True)
    out_of_stock_products = all_products.exclude(id__in=products_with_stock)
    
    product_stock_summary = []
    for product in all_products[:PAGINATE_BY_DEFAULT]:
        total = product.total_stock()
        if total > STOCK_ZERO:
            product_stock_summary.append({
                'product': product,
                'total_stock': total,
                'variants_count': product.variants.filter(is_active=True).count(),
            })
    
    context = {
        'low_stock_variants': low_stock_variants,
        'out_of_stock_variants': out_of_stock_variants,
        'out_of_stock_products': out_of_stock_products,
        'product_stock_summary': product_stock_summary,
        'low_stock_count': low_stock_variants.count(),
        'out_of_stock_variants_count': out_of_stock_variants.count(),
        'out_of_stock_products_count': out_of_stock_products.count(),
    }
    return render(request, TEMPLATE_STOCK_DASHBOARD, context)


class BaseProductListView(PaginationMixin, FilterMixin, ListView):
    """Clase base para vistas que listan productos con filtros comunes."""
    
    def apply_search_filter(self, qs):
        """Aplica filtro de búsqueda por nombre o descripción."""
        search = self.request.GET.get(QUERY_PARAM_SEARCH, '')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return qs
    
    def apply_price_range_filter(self, qs):
        """Aplica filtro de rango de precios."""
        min_price = self.request.GET.get(QUERY_PARAM_MIN_PRICE, '')
        max_price = self.request.GET.get(QUERY_PARAM_MAX_PRICE, '')
        
        if min_price and min_price.isdigit():
            qs = qs.filter(price__gte=int(min_price))
        
        if max_price and max_price.isdigit():
            qs = qs.filter(price__lte=int(max_price))
        
        return qs
    
    def apply_ordering(self, qs, default_order=ORDER_BY_CREATED_AT):
        """Aplica ordenamiento al queryset."""
        order_by = self.request.GET.get(QUERY_PARAM_ORDER_BY, default_order)
        allowed_orders = [choice[0] for choice in ORDER_CHOICES_CATALOG]
        if order_by in allowed_orders:
            return qs.order_by(order_by)
        return qs.order_by(default_order)
    
    def get_base_queryset(self):
        """Retorna el queryset base con prefetch relacionado."""
        return super().get_queryset().filter(is_active=PRODUCT_FILTER_ACTIVE).select_related(
            'category'
        ).prefetch_related(
            'product_colors', 'product_colors__images', 'variants', 'variants__size'
        )
    
    def apply_common_filters(self, qs):
        """Aplica todos los filtros comunes a un queryset."""
        qs = self.apply_search_filter(qs)
        qs = self.apply_price_range_filter(qs)
        qs = self.apply_ordering(qs)
        return qs
    

class ProductCatalogView(BaseProductListView):
    """
    HU-004: Consultar catálogo
    HU-007: Filtrar productos
    """
    model = Product
    template_name = TEMPLATE_CATALOG
    context_object_name = CONTEXT_PRODUCTS
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (QUERY_PARAM_CATEGORY, 'category__slug', 'exact'),
        (QUERY_PARAM_PRODUCT_TYPE, 'product_type', 'exact'),
    ]
    
    def get_queryset(self):
        # HU-004 | ESCENARIO 1 | H | Catálogo cargado exitosamente con productos activos
        # HU-007 | ESCENARIO 1,2,3,4 | H | Filtros aplicados (talla, precio, tipo, combinados)
        qs = self.get_base_queryset()
        qs = self.apply_common_filters(qs)
        return qs
    
    def get_context_data(self, **kwargs):
        # HU-004 | ESCENARIO 3 | H | Paginación configurada
        # HU-007 | ESCENARIO 5 | A | Sin resultados con filtros (template muestra mensaje)
        # HU-007 | ESCENARIO 6 | H | Limpiar filtros (botón con clean_url)
        context = super().get_context_data(**kwargs)
        
        categories = Category.objects.all().order_by(ORDER_BY_SORT_ORDER)
        
        price_range = Product.objects.filter(is_active=True).aggregate(
            min_price=Min('price'), max_price=Max('price')
        )
        
        # Available product types (without duplicates)
        product_types = list(set(
            Product.objects.filter(is_active=True).values_list('product_type', flat=True)
        ))
        # Filter empty values
        product_types = [pt for pt in product_types if pt]
        
        context['categories'] = categories
        context['current_category'] = self.request.GET.get(QUERY_PARAM_CATEGORY, '')
        context['current_search'] = self.request.GET.get(QUERY_PARAM_SEARCH, '')
        context['current_min_price'] = self.request.GET.get(QUERY_PARAM_MIN_PRICE, '')
        context['current_max_price'] = self.request.GET.get(QUERY_PARAM_MAX_PRICE, '')
        context['current_product_type'] = self.request.GET.get(QUERY_PARAM_PRODUCT_TYPE, '')
        context['current_order_by'] = self.request.GET.get(QUERY_PARAM_ORDER_BY, ORDER_BY_CREATED_AT)
        context['min_price_global'] = int(price_range['min_price'] or 0)
        context['max_price_global'] = int(price_range['max_price'] or 1000000)
        context['product_types'] = product_types
        context['product_type_labels'] = {pt: PRODUCT_TYPES_DISPLAY.get(pt, pt) for pt in product_types}
        context['filter_config'] = FILTER_CONFIG_DEFAULT
        context['order_choices'] = ORDER_CHOICES_CATALOG
        context['has_active_filters'] = any([
            self.request.GET.get(QUERY_PARAM_SEARCH),
            self.request.GET.get(QUERY_PARAM_CATEGORY),
            self.request.GET.get(QUERY_PARAM_MIN_PRICE),
            self.request.GET.get(QUERY_PARAM_MAX_PRICE),
            self.request.GET.get(QUERY_PARAM_PRODUCT_TYPE),
        ])
        context['clean_url'] = reverse('products:catalog')
        
        return context


class CollectionListViewPublic(PaginationMixin, FilterMixin, ListView):
    """
    HU-005: Consultar colecciones (público)
    """
    model = Collection
    template_name = TEMPLATE_COLLECTIONS_LIST_PUBLIC
    context_object_name = 'collections'
    paginate_by = PAGINATE_BY_COLLECTIONS
    
    filters = [
        (QUERY_PARAM_PRODUCT_TYPE, 'products__product_type', 'exact'),
    ]
    
    def _apply_search_filter(self, qs):
        # HU-005 | ESCENARIO 1 | H | Búsqueda por nombre o descripción
        search = self.request.GET.get(QUERY_PARAM_SEARCH, '')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return qs
    
    def _apply_status_filter(self, qs):
        # HU-005 | ESCENARIO 2 | A | Colección con fecha futura (status=borrador) se muestra como "Próximamente"
        # HU-005 | ESCENARIO 3 | A | Colección expirada (status=archivada) se oculta o muestra como pasada
        status_filter = self.request.GET.get(QUERY_PARAM_STATUS, '')
        if status_filter == STATUS_FILTER_ACTIVE:
            qs = qs.filter(status=STATUS_PUBLISHED)
        elif status_filter == STATUS_FILTER_UPCOMING:
            qs = qs.filter(status=STATUS_DRAFT)
        elif status_filter == STATUS_FILTER_ARCHIVED:
            qs = qs.filter(status=STATUS_ARCHIVED)
        return qs
    
    def _apply_price_range_filter(self, qs):
        # HU-005 | ESCENARIO 1 | H | Filtro por rango de precios de productos en colección
        min_price = self.request.GET.get(QUERY_PARAM_MIN_PRICE, '')
        max_price = self.request.GET.get(QUERY_PARAM_MAX_PRICE, '')
        
        if min_price and min_price.isdigit():
            qs = qs.filter(products__price__gte=int(min_price)).distinct()
        
        if max_price and max_price.isdigit():
            qs = qs.filter(products__price__lte=int(max_price)).distinct()
        
        return qs
    
    def _apply_product_count_filter(self, qs):
        # HU-005 | ESCENARIO 1 | H | Filtro por cantidad de productos en colección
        product_count_min = self.request.GET.get(QUERY_PARAM_PRODUCT_COUNT_MIN, '')
        product_count_max = self.request.GET.get(QUERY_PARAM_PRODUCT_COUNT_MAX, '')
        
        if product_count_min and product_count_min.isdigit():
            qs = qs.annotate(product_count=Count('products')).filter(product_count__gte=int(product_count_min))
        
        if product_count_max and product_count_max.isdigit():
            if not product_count_min:
                qs = qs.annotate(product_count=Count('products'))
            qs = qs.filter(product_count__lte=int(product_count_max))
        
        return qs
    
    def _apply_date_filter(self, qs):
        """Apply date filter (last month, quarter, semester, year, upcoming)."""
        # HU-005 | ESCENARIO 2 | A | Filtro "Próximas" (start_date > now, status=borrador)
        # HU-005 | ESCENARIO 3 | A | Filtro por fecha de inicio (colecciones recientes)
        date_filter = self.request.GET.get(QUERY_PARAM_DATE_FILTER, '')
        now = timezone.now()
        hoy = now.date()
        
        if date_filter == DATE_FILTER_LAST_MONTH:
            qs = qs.filter(start_date__gte=now - timedelta(days=30))
        elif date_filter == DATE_FILTER_LAST_QUARTER:
            qs = qs.filter(start_date__gte=now - timedelta(days=90))
        elif date_filter == DATE_FILTER_LAST_SEMESTER:
            qs = qs.filter(start_date__gte=now - timedelta(days=180))
        elif date_filter == DATE_FILTER_LAST_YEAR:
            qs = qs.filter(start_date__gte=now - timedelta(days=365))
        elif date_filter == DATE_FILTER_UPCOMING:
            qs = qs.filter(
                start_date__date__gt=hoy,
                is_active=True,
                status=STATUS_DRAFT
            )
        
        return qs
    
    def _apply_ordering(self, qs):
        """Apply ordering to the queryset."""
        order_by = self.request.GET.get(QUERY_PARAM_ORDER_BY, ORDER_BY_CREATED_AT)
        allowed_orders = [choice[0] for choice in ORDER_CHOICES_COLLECTIONS]
        if order_by in allowed_orders:
            return qs.order_by(order_by)
        return qs.order_by(ORDER_BY_CREATED_AT)
    
    def get_queryset(self):
        """Build the queryset with all filters applied."""
        # HU-005 | ESCENARIO 1 | H | Listado de colecciones activas cargado
        # HU-005 | ESCENARIO 4 | A | Sin colecciones activas → template muestra mensaje
        qs = super().get_queryset()
        hoy = timezone.now().date()
        qs = qs.filter(is_active=True)
    
        date_filter = self.request.GET.get(QUERY_PARAM_DATE_FILTER, '')
        
        if date_filter == DATE_FILTER_UPCOMING:
            qs = qs.filter(
                status=STATUS_DRAFT,
                start_date__date__gt=hoy
            )
        else:
            qs = qs.filter(status=STATUS_PUBLISHED)
            qs = qs.filter(
                Q(start_date__isnull=True) |
                Q(start_date__date__lte=hoy)
            )
        
        qs = self._apply_search_filter(qs)
        qs = self._apply_price_range_filter(qs)
        qs = self._apply_product_count_filter(qs)
        qs = self._apply_date_filter(qs)
        qs = self._apply_ordering(qs)
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Global price range
        price_range = ProductVariant.objects.filter(
            is_active=True,
            product__is_active=True
        ).aggregate(
            min_price=Min('product__price'),
            max_price=Max('product__price')
        )
        
        # Available product types
        product_types = Product.objects.filter(
            is_active=True
        ).values_list('product_type', flat=True).distinct()
        
        # Build table rows
        rows = []
        for collection in context['collections']:
            product_count = collection.products.filter(is_active=True).count()
            price_range_collection = collection.products.filter(
                is_active=True
            ).aggregate(
                min_price=Min('price'),
                max_price=Max('price')
            )
            
            start_date_str = collection.start_date.strftime(DATE_FORMAT_DAY_MONTH_YEAR) if collection.start_date else '-'
            end_date_str = collection.end_date.strftime(DATE_FORMAT_DAY_MONTH_YEAR) if collection.end_date else '-'

            rows.append({
                'pk': collection.pk,
                'values': [
                    mark_safe(
                        f'<div class="flex flex-col">'
                        f'<span class="font-medium">{collection.name}</span>'
                        f'<span class="text-xs text-gray-500">{collection.get_status_display()}</span>'
                        f'</div>'
                    ),
                    mark_safe(
                        f'<img src="{collection.cover_image.url}" class="w-12 h-12 object-cover rounded" />'
                        if collection.cover_image else f'<span class="text-gray-400">{UI_NO_IMAGE}</span>'
                    ),
                    product_count,
                    f'${price_range_collection["min_price"] or 0:,.0f} - ${price_range_collection["max_price"] or 0:,.0f}',
                    mark_safe(
                        f'<div class="text-sm">'
                        f'<div>Inicio: {start_date_str}</div>'
                        f'<div>Fin: {end_date_str}</div>'
                        f'</div>'
                    ),
                ]
            })
        
        context.update({
            'rows': rows,
            'headers': HEADERS_COLLECTION,
            'search_value': self.request.GET.get(QUERY_PARAM_SEARCH, ''),
            'current_status': self.request.GET.get(QUERY_PARAM_STATUS, ''),
            'current_min_price': self.request.GET.get(QUERY_PARAM_MIN_PRICE, ''),
            'current_max_price': self.request.GET.get(QUERY_PARAM_MAX_PRICE, ''),
            'min_price_global': int(price_range['min_price'] or 0),
            'max_price_global': int(price_range['max_price'] or 1000000),
            'current_product_count_min': self.request.GET.get(QUERY_PARAM_PRODUCT_COUNT_MIN, ''),
            'current_product_count_max': self.request.GET.get(QUERY_PARAM_PRODUCT_COUNT_MAX, ''),
            'current_date_filter': self.request.GET.get(QUERY_PARAM_DATE_FILTER, ''),
            'current_product_type': self.request.GET.get(QUERY_PARAM_PRODUCT_TYPE, ''),
            'current_order_by': self.request.GET.get(QUERY_PARAM_ORDER_BY, ORDER_BY_CREATED_AT),
            'product_types': list(product_types),
            'product_type_labels': {pt: PRODUCT_TYPES_DISPLAY.get(pt, pt) for pt in product_types},
            'status_choices': STATUS_FILTER_CHOICES,
            'order_choices': ORDER_CHOICES_COLLECTIONS,
            'filter_config': FILTER_CONFIG_WITH_STATUS,
            'has_active_filters': any([
                self.request.GET.get(QUERY_PARAM_SEARCH),
                self.request.GET.get(QUERY_PARAM_STATUS),
                self.request.GET.get(QUERY_PARAM_MIN_PRICE),
                self.request.GET.get(QUERY_PARAM_MAX_PRICE),
                self.request.GET.get(QUERY_PARAM_PRODUCT_COUNT_MIN),
                self.request.GET.get(QUERY_PARAM_PRODUCT_COUNT_MAX),
                self.request.GET.get(QUERY_PARAM_DATE_FILTER),
                self.request.GET.get(QUERY_PARAM_PRODUCT_TYPE),
            ]),
            'clean_url': reverse('products:collections_list'),            
            'now': timezone.now(),
        })
        
        return context


class CollectionDetailView(BaseProductListView):
    """
    HU-005: Consultar detalle de colección
    HU-006: Ver productos de una colección
    """
    model = Product
    template_name = TEMPLATE_COLLECTION_DETAIL
    context_object_name = CONTEXT_PRODUCTS
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (QUERY_PARAM_PRODUCT_TYPE, 'product_type', 'exact'),
    ]
    
    def dispatch(self, request, *args, **kwargs):
        # HU-005 | ESCENARIO 2 | A | Colección con fecha futura (status=borrador) no es accesible
        # HU-005 | ESCENARIO 3 | A | Colección expirada (status=archivada) no es accesible
        self.collection = get_object_or_404(
            Collection, 
            slug=kwargs['slug'], 
            status=STATUS_PUBLISHED, 
            is_active=True
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # HU-006 | ESCENARIO 1 | H | Productos de la colección filtrados
        qs = super().get_queryset().filter(is_active=PRODUCT_FILTER_ACTIVE)
        qs = qs.filter(collections=self.collection)
        qs = self.apply_common_filters(qs)
        return qs
    
    def _sanitize_css(self, raw_css):
        if not raw_css:
            return ''
        
        dangerous = re.compile(
            r'(javascript:|expression\(|behavior\s*:|vbscript:|<script|</script|on\w+\s*=)',
            re.IGNORECASE
        )
        cleaned = dangerous.sub('', raw_css)
        
        if len(cleaned) > 5000:
            cleaned = cleaned[:5000]
        
        return mark_safe(cleaned)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # HU-006 | ESCENARIO 2 | H | Producto con colección especial (estilos visuales aplicados)
        context['collection'] = self.collection
        context['total_products'] = self.get_queryset().count()
        
        price_range = self.collection.products.filter(
            is_active=True
        ).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        
        product_types = self.collection.products.filter(
            is_active=True
        ).values_list('product_type', flat=True).distinct()
        
        context['current_search'] = self.request.GET.get(QUERY_PARAM_SEARCH, '')
        context['current_min_price'] = self.request.GET.get(QUERY_PARAM_MIN_PRICE, '')
        context['current_max_price'] = self.request.GET.get(QUERY_PARAM_MAX_PRICE, '')
        context['current_product_type'] = self.request.GET.get(QUERY_PARAM_PRODUCT_TYPE, '')
        context['current_order_by'] = self.request.GET.get(QUERY_PARAM_ORDER_BY, ORDER_BY_CREATED_AT)
        
        context['min_price_global'] = int(price_range['min_price'] or 0)
        context['max_price_global'] = int(price_range['max_price'] or 1000000)
        
        context['product_types'] = list(product_types)
        context['product_type_labels'] = {pt: PRODUCT_TYPES_DISPLAY.get(pt, pt) for pt in product_types}
        
        context['filter_config'] = FILTER_CONFIG_DEFAULT
        
        context['order_choices'] = ORDER_CHOICES_CATALOG
        
        context['has_active_filters'] = any([
            self.request.GET.get(QUERY_PARAM_SEARCH),
            self.request.GET.get(QUERY_PARAM_MIN_PRICE),
            self.request.GET.get(QUERY_PARAM_MAX_PRICE),
            self.request.GET.get(QUERY_PARAM_PRODUCT_TYPE),
        ])
        
        context['clean_url'] = reverse('products:collection_detail', kwargs={'slug': self.collection.slug})
        context['now'] = timezone.now()
        
        # HU-006 | ESCENARIO 2 | H | CSS personalizado de la colección sanitizado
        context['safe_custom_css'] = self._sanitize_css(self.collection.custom_css)
        
        return context


@require_GET
def product_detail(request, slug):
    """
    HU-006: Consultar detalle de producto
    HU-008: Consultar disponibilidad de talla
    """
    # HU-006 | ESCENARIO 1 | H | Producto existe y está activo
    # HU-006 | ESCENARIO 4 | E | Producto no existe o inactivo → HTTP 404
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    context = {
        CONTEXT_PRODUCT: product,
        **build_gallery_context(product),
        **build_variants_context(product),  # HU-008: tallas con stock
        'related_products': get_related_products(product),
    }
    return render(request, TEMPLATE_PRODUCT_DETAIL, context)


def build_gallery_context(product):
    """
    HU-006: Construir galería de imágenes del producto
    """
    # HU-006 | ESCENARIO 1 | H | Imágenes del producto cargadas
    product_colors = product.product_colors.filter(
        is_active=True
    ).prefetch_related('images').order_by(ORDER_BY_SORT_ORDER)
    
    gallery_images = []
    featured_image = None
    
    for pc in product_colors:
        for img in pc.get_images():
            image_url = img.image.url if img.image else ''
            gallery_images.append({
                'image': image_url,
                'color_id': pc.color.id,
                'color_name': pc.color.name,
                'color_code': pc.color.code or '#cccccc',
                'is_featured': pc.featured_image == img,
            })
            if not featured_image and pc.featured_image == img:
                featured_image = image_url
    
    if not featured_image and gallery_images:
        featured_image = gallery_images[0]['image']
    
    return {
        'gallery_images': gallery_images,
        'gallery_images_json': json.dumps(gallery_images),
        'featured_image': featured_image,
    }


def build_variants_context(product):
    """
    HU-008: Consultar disponibilidad de talla
    """
    variants = product.variants.filter(
        is_active=True
    ).select_related('product_color', 'size')
    
    variants_data = []
    unique_colors = []
    unique_sizes = []
    seen_color_ids = set()
    seen_size_ids = set()
    
    for variant in variants:
        stock_display, stock_message = get_stock_display(variant.stock)
        color = variant.product_color.color
        size = variant.size
        
        variants_data.append({
            'id': variant.id,
            'color_id': color.id,
            'color_name': color.name,
            'color_code': color.code or '#cccccc',
            'size_id': size.id,
            'size_name': size.name,
            'stock': variant.stock,
            # HU-008 | ESCENARIO 1 | H | Talla disponible (stock > 0) → stock_display='available'
            # HU-008 | ESCENARIO 2 | A | Talla agotada (stock = 0) → stock_display='out_of_stock'
            'stock_display': stock_display,
            'stock_message': stock_message,
            'price': float(product.price),
            'image': variant.product_color.featured_image.image.url if variant.product_color.featured_image and variant.product_color.featured_image.image else '',
        })
        
        if color.id not in seen_color_ids:
            seen_color_ids.add(color.id)
            unique_colors.append({
                'id': color.id,
                'name': color.name,
                'code': color.code or '#cccccc',
            })
        
        if size.id not in seen_size_ids:
            seen_size_ids.add(size.id)
            unique_sizes.append({
                'id': size.id,
                'name': size.name,
            })
    
    # HU-008 | ESCENARIO 3 | A | Producto sin tallas configuradas → variants vacío, template muestra mensaje
    return {
        CONTEXT_VARIANTS: variants,
        'unique_colors': unique_colors,
        'unique_sizes': unique_sizes,
        'variants_json': json.dumps(variants_data),
    }


def get_related_products(product, limit=PRODUCT_LIMIT_RELATED):
    """
    HU-006: Productos relacionados (misma categoría)
    """
    # HU-006 | ESCENARIO 1 | H | Productos relacionados cargados
    return Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).select_related(
        'category'
    ).prefetch_related(
        'product_colors', 'product_colors__images'
    )[:limit]


# =============================================================================
# SIZE CRUD VIEWS (HU-058 a HU-062)
# =============================================================================

class SizeListView(StaffPermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """
    HU-058: Listar tallas
    """
    model = Size
    template_name = TEMPLATE_SIZE_LIST
    context_object_name = 'sizes'
    permission_required = 'products.view_size'  # HU-058 | ESCENARIO 2 | E | Sin permisos
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (FILTER_NAME, FILTER_NAME, 'icontains'),
        ('sort_order', 'sort_order', 'exact'),
    ]

    def get_context_data(self, **kwargs):
        # HU-058 | ESCENARIO 1 | H | Lista de tallas cargada exitosamente
        # HU-058 | ESCENARIO 3 | A | Sin tallas → template muestra mensaje
        context = super().get_context_data(**kwargs)
        rows = []
        for size in context['sizes']:
            rows.append({
                'pk': size.pk,
                'values': [size.name, size.sort_order],
            })
        context['rows'] = rows
        context['headers'] = HEADERS_SIZE
        return context


class SizeCreateView(StaffPermissionRequiredMixin, CreateView):
    """
    HU-059: Crear talla
    """
    model = Size
    form_class = SizeCreateForm
    template_name = TEMPLATE_SIZE_FORM
    permission_required = 'products.add_size'  # HU-059 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_SIZE_LIST)
    
    def form_valid(self, form):
        # HU-059 | ESCENARIO 1 | H | Talla creada exitosamente
        messages.success(self.request, MSG_SIZE_CREATED.format(name=form.instance.name))
        return super().form_valid(form)
    # HU-059 | ESCENARIO 2 | A | Errores en formulario (manejado por CreateView)


class SizeUpdateView(StaffPermissionRequiredMixin, UpdateView):
    """
    HU-060: Editar talla
    """
    model = Size
    form_class = SizeUpdateForm
    template_name = TEMPLATE_SIZE_FORM
    permission_required = 'products.change_size'  # HU-060 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_SIZE_LIST)
    
    def form_valid(self, form):
        # HU-060 | ESCENARIO 1 | H | Talla actualizada exitosamente
        messages.success(self.request, MSG_SIZE_UPDATED.format(name=form.instance.name))
        return super().form_valid(form)
    # HU-060 | ESCENARIO 2 | A | Errores en formulario
    # HU-060 | ESCENARIO 4 | E | Talla no existe → HTTP 404


class SizeDeleteView(StaffPermissionRequiredMixin, SortableDeleteMixin, DeleteView):
    """
    HU-061: Eliminar talla
    """
    model = Size
    form_class = SizeDeleteForm
    template_name = TEMPLATE_SIZE_CONFIRM_DELETE
    permission_required = 'products.delete_size'  # HU-061 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_SIZE_LIST)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['size'] = self.get_object()
        return kwargs
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.delete(request, *args, **kwargs)
        # HU-061 | ESCENARIO 2 | A | Cancelar eliminación
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        size = self.get_object()
        size_name = size.name
        # HU-061 | ESCENARIO 1 | H | Talla eliminada exitosamente
        size.delete()
        messages.success(request, MSG_SIZE_DELETED.format(name=size_name))
        return redirect(self.success_url)
    # HU-061 | ESCENARIO 4 | A | Talla con variantes activas → validación en form


class SizeImportView(StaffPermissionRequiredMixin, View):
    """
    HU-062: Importar tallas desde CSV/Excel
    """
    permission_required = 'products.add_size'  # HU-062 | ESCENARIO 5 | E | Sin permisos
    
    def get(self, request):
        # HU-062 | ESCENARIO 1 | H | Descargar plantilla (GET)
        importer = SizeImporter(request, None)
        context = {
            'headers': importer.get_template_headers(),
            'example_data': importer.get_example_data(),
            'required_columns': importer.required_columns,
        }
        return render(request, TEMPLATE_SIZE_IMPORT, context)
    
    def post(self, request):
        file_obj = request.FILES.get(IMPORT_FILE_FIELD)
        update_existing = request.POST.get(IMPORT_UPDATE_EXISTING_FIELD) == 'on'
        
        # HU-062 | ESCENARIO 4 | A | Archivo vacío o no seleccionado
        if not file_obj:
            messages.error(request, MSG_IMPORT_NO_FILE)
            return redirect(PRODUCTS_SIZE_IMPORT)
        
        importer = SizeImporter(request, file_obj, update_existing=update_existing)
        results = importer.run()
        importer.add_messages()
        
        request.session['import_results'] = results
        
        # HU-062 | ESCENARIO 2 | H | Importación exitosa
        # HU-062 | ESCENARIO 3 | A | Importación con fallos parciales
        return render(request, TEMPLATE_SIZE_IMPORT_RESULT, {'results': results})


@require_GET
def size_template(request):
    """
    HU-062 | ESCENARIO 1 | H | Descargar plantilla de tallas
    """
    return generate_csv_response(
        filename=IMPORT_TEMPLATE_FILENAME_SIZE,
        headers=IMPORT_TEMPLATE_COLUMNS_SIZE,
        rows=IMPORT_EXAMPLE_DATA_SIZE
    )


# =============================================================================
# CATEGORY CRUD VIEWS (HU-063 a HU-067)
# =============================================================================

class CategoryListView(StaffPermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """
    HU-063: Listar categorías
    """
    model = Category
    template_name = TEMPLATE_CATEGORY_LIST
    context_object_name = 'categories'
    permission_required = 'products.view_category'  # HU-063 | ESCENARIO 2 | E | Sin permisos
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (FILTER_NAME, FILTER_NAME, 'icontains'),
        ('slug', 'slug', 'icontains'),
        ('sort_order', 'sort_order', 'exact'),
    ]
    
    def get_context_data(self, **kwargs):
        # HU-063 | ESCENARIO 1 | H | Lista de categorías cargada exitosamente
        # HU-063 | ESCENARIO 3 | A | Sin categorías → template muestra mensaje
        context = super().get_context_data(**kwargs)
        rows = []
        for category in context['categories']:
            rows.append({
                'pk': category.pk,
                'values': [category.name, category.slug, category.sort_order],
            })
        context['rows'] = rows
        context['headers'] = HEADERS_CATEGORY
        return context


class CategoryCreateView(StaffPermissionRequiredMixin, CreateView):
    """
    HU-064: Crear categoría
    """
    model = Category
    form_class = CategoryCreateForm
    template_name = TEMPLATE_CATEGORY_FORM
    permission_required = 'products.add_category'  # HU-064 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_CATEGORY_LIST)
    
    def form_valid(self, form):
        # HU-064 | ESCENARIO 1 | H | Categoría creada exitosamente
        messages.success(self.request, MSG_CATEGORY_CREATED.format(name=form.instance.name))
        return super().form_valid(form)
    # HU-064 | ESCENARIO 2 | A | Errores en formulario


class CategoryUpdateView(StaffPermissionRequiredMixin, UpdateView):
    """
    HU-065: Editar categoría
    """
    model = Category
    form_class = CategoryUpdateForm
    template_name = TEMPLATE_CATEGORY_FORM
    permission_required = 'products.change_category'  # HU-065 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_CATEGORY_LIST)
    
    def form_valid(self, form):
        # HU-065 | ESCENARIO 1 | H | Categoría actualizada exitosamente
        messages.success(self.request, MSG_CATEGORY_UPDATED.format(name=form.instance.name))
        return super().form_valid(form)
    # HU-065 | ESCENARIO 2 | A | Errores en formulario
    # HU-065 | ESCENARIO 4 | E | Categoría no existe → HTTP 404


class CategoryDeleteView(StaffPermissionRequiredMixin, DeleteView):
    """
    HU-066: Eliminar categoría
    """
    model = Category
    form_class = CategoryDeleteForm
    template_name = TEMPLATE_CATEGORY_CONFIRM_DELETE
    permission_required = 'products.delete_category'  # HU-066 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_CATEGORY_LIST)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['category'] = self.get_object()
        return kwargs
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.delete(request, *args, **kwargs)
        # HU-066 | ESCENARIO 2 | A | Cancelar eliminación
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        category_name = category.name
        # HU-066 | ESCENARIO 1 | H | Categoría eliminada exitosamente
        category.delete()
        messages.success(request, MSG_CATEGORY_DELETED.format(name=category_name))
        return redirect(self.success_url)
    # HU-066 | ESCENARIO 4 | A | Categoría con productos activos → validación en form


class CategoryImportView(StaffPermissionRequiredMixin, View):
    """
    HU-067: Importar categorías desde CSV/Excel
    """
    permission_required = 'products.add_category'  # HU-067 | ESCENARIO 5 | E | Sin permisos
    
    def get(self, request):
        # HU-067 | ESCENARIO 1 | H | Descargar plantilla
        importer = CategoryImporter(request, None)
        context = {
            'headers': importer.get_template_headers(),
            'example_data': importer.get_example_data(),
            'required_columns': importer.required_columns,
        }
        return render(request, TEMPLATE_CATEGORY_IMPORT, context)
    
    def post(self, request):
        file_obj = request.FILES.get(IMPORT_FILE_FIELD)
        update_existing = request.POST.get(IMPORT_UPDATE_EXISTING_FIELD) == 'on'
        
        # HU-067 | ESCENARIO 4 | A | Archivo vacío
        if not file_obj:
            messages.error(request, MSG_IMPORT_NO_FILE)
            return redirect(PRODUCTS_CATEGORY_IMPORT)
        
        importer = CategoryImporter(request, file_obj, update_existing=update_existing)
        results = importer.run()
        importer.add_messages()
        
        # HU-067 | ESCENARIO 2 | H | Importación exitosa
        # HU-067 | ESCENARIO 3 | A | Importación con fallos parciales
        context = {'results': results}
        return render(request, TEMPLATE_CATEGORY_IMPORT_RESULT, context)


@require_GET
def category_template(request):
    """
    HU-067 | ESCENARIO 1 | H | Descargar plantilla de categorías
    """
    return generate_csv_response(
        filename=IMPORT_TEMPLATE_FILENAME_CATEGORY,
        headers=IMPORT_TEMPLATE_COLUMNS_CATEGORY,
        rows=IMPORT_EXAMPLE_DATA_CATEGORY
    )


# =============================================================================
# COLOR CRUD VIEWS (HU-068 a HU-072)
# =============================================================================

class ColorListView(StaffPermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """
    HU-068: Listar colores
    """
    model = Color
    template_name = TEMPLATE_COLOR_LIST
    context_object_name = 'colors'
    permission_required = 'products.view_color'  # HU-068 | ESCENARIO 2 | E | Sin permisos
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (FILTER_NAME, FILTER_NAME, 'icontains'),
        ('code', 'code', 'icontains'),
        ('sort_order', 'sort_order', 'exact'),
    ]
    
    def get_context_data(self, **kwargs):
        # HU-068 | ESCENARIO 1 | H | Lista de colores cargada exitosamente
        # HU-068 | ESCENARIO 3 | A | Sin colores → template muestra mensaje
        context = super().get_context_data(**kwargs)
        rows = []
        for color in context['colors']:
            rows.append({
                'pk': color.pk,
                'values': [
                    color.name,
                    mark_safe(
                        f'<div class="flex items-center gap-2">'
                        f'<div class="w-6 h-6 rounded-full border" style="background-color: {color.code};"></div>'
                        f'<span>{color.code}</span>'
                        f'</div>'
                    ),
                    color.sort_order
                ],
            })
        context['rows'] = rows
        context['headers'] = HEADERS_COLOR
        return context


class ColorCreateView(StaffPermissionRequiredMixin, CreateView):
    """
    HU-069: Crear color
    """
    model = Color
    form_class = ColorCreateForm
    template_name = TEMPLATE_COLOR_FORM
    permission_required = 'products.add_color'  # HU-069 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_COLOR_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_COLOR_LIST
        return context
    
    def form_valid(self, form):
        # HU-069 | ESCENARIO 1 | H | Color creado exitosamente
        messages.success(self.request, MSG_COLOR_CREATED.format(name=form.instance.name))
        return super().form_valid(form)
    # HU-069 | ESCENARIO 2 | A | Errores en formulario (nombre duplicado, código inválido)


class ColorUpdateView(StaffPermissionRequiredMixin, UpdateView):
    """
    HU-070: Editar color
    """
    model = Color
    form_class = ColorUpdateForm
    template_name = TEMPLATE_COLOR_FORM
    permission_required = 'products.change_color'  # HU-070 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_COLOR_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_COLOR_LIST
        return context
    
    def form_valid(self, form):
        # HU-070 | ESCENARIO 1 | H | Color actualizado exitosamente
        messages.success(self.request, MSG_COLOR_UPDATED.format(name=form.instance.name))
        return super().form_valid(form)
    # HU-070 | ESCENARIO 2 | A | Errores en formulario
    # HU-070 | ESCENARIO 4 | E | Color no existe → HTTP 404


class ColorDeleteView(StaffPermissionRequiredMixin, SortableDeleteMixin, DeleteView):
    """
    HU-071: Eliminar color
    """
    model = Color
    form_class = ColorDeleteForm
    template_name = TEMPLATE_COLOR_CONFIRM_DELETE
    permission_required = 'products.delete_color'  # HU-071 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_COLOR_LIST)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['color'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_OBJECT_NAME] = 'Color'
        context[CONTEXT_OBJECT_DISPLAY] = self.get_object().name
        context[CONTEXT_CANCEL_URL] = PRODUCTS_COLOR_LIST
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.delete(request, *args, **kwargs)
        # HU-071 | ESCENARIO 2 | A | Cancelar eliminación
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        color = self.get_object()
        color_name = color.name
        # HU-071 | ESCENARIO 1 | H | Color eliminado exitosamente
        color.delete()
        messages.success(request, MSG_COLOR_DELETED.format(name=color_name))
        return redirect(self.success_url)
    # HU-071 | ESCENARIO 4 | A | Color con variantes activas → validación en form


class ColorImportView(StaffPermissionRequiredMixin, View):
    """
    HU-072: Importar colores desde CSV/Excel
    """
    permission_required = 'products.add_color'  # HU-072 | ESCENARIO 5 | E | Sin permisos
    
    def get(self, request):
        # HU-072 | ESCENARIO 1 | H | Descargar plantilla
        importer = ColorImporter(request, None)
        context = {
            'headers': importer.get_template_headers(),
            'example_data': importer.get_example_data(),
            'required_columns': importer.required_columns,
        }
        return render(request, TEMPLATE_COLOR_IMPORT, context)
    
    def post(self, request):
        file_obj = request.FILES.get(IMPORT_FILE_FIELD)
        update_existing = request.POST.get(IMPORT_UPDATE_EXISTING_FIELD) == 'on'
        
        # HU-072 | ESCENARIO 4 | A | Archivo vacío
        if not file_obj:
            messages.error(request, MSG_IMPORT_NO_FILE)
            return redirect(PRODUCTS_COLOR_IMPORT)
        
        importer = ColorImporter(request, file_obj, update_existing=update_existing)
        results = importer.run()
        importer.add_messages()
        
        # HU-072 | ESCENARIO 2 | H | Importación exitosa
        # HU-072 | ESCENARIO 3 | A | Importación con fallos parciales
        context = {'results': results}
        return render(request, TEMPLATE_COLOR_IMPORT_RESULT, context)


@require_GET
def color_template(request):
    """
    HU-072 | ESCENARIO 1 | H | Descargar plantilla de colores
    """
    return generate_csv_response(
        filename=IMPORT_TEMPLATE_FILENAME_COLOR,
        headers=IMPORT_TEMPLATE_COLUMNS_COLOR,
        rows=IMPORT_EXAMPLE_DATA_COLOR
    )


# =============================================================================
# PRODUCT IMAGE CRUD VIEWS (HU-073 a HU-076)
# =============================================================================

class ProductImageListView(StaffPermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """
    HU-073: Listar imágenes de producto
    """
    model = ProductImage
    template_name = TEMPLATE_PRODUCTIMAGE_LIST
    context_object_name = 'images'
    permission_required = 'products.view_productimage'  # HU-073 | ESCENARIO 2 | E | Sin permisos
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        ('alt_text', 'alt_text', 'icontains'),
        ('created_at', 'created_at', 'date'),
    ]
    
    def get_context_data(self, **kwargs):
        # HU-073 | ESCENARIO 1 | H | Lista de imágenes cargada exitosamente
        # HU-073 | ESCENARIO 3 | A | Sin imágenes → template muestra mensaje
        context = super().get_context_data(**kwargs)
        rows = []
        for img in context['images']:
            alt_text = img.alt_text or f"Imagen {img.pk}"
            rows.append({
                'pk': img.pk,
                'values': [
                    mark_safe(f'<img src="{img.image.url}" alt="{alt_text}" class="w-16 h-16 object-cover rounded-lg">'),
                    alt_text,
                    img.created_at.strftime(DATE_FORMAT_DISPLAY),
                ],
            })
        context['rows'] = rows
        context['headers'] = HEADERS_PRODUCT_IMAGE
        return context


class ProductImageCreateView(StaffPermissionRequiredMixin, CreateView):
    """
    HU-074: Subir imagen de producto
    """
    model = ProductImage
    form_class = ProductImageCreateForm
    template_name = TEMPLATE_PRODUCTIMAGE_FORM
    permission_required = 'products.add_productimage'  # HU-074 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_IMAGE_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_IMAGE_LIST
        return context
    
    def form_valid(self, form):
        image_name = form.instance.image.name.split('/')[-1]
        # HU-074 | ESCENARIO 1 | H | Imagen subida exitosamente
        messages.success(self.request, MSG_PRODUCT_IMAGE_UPLOADED.format(name=image_name))
        return super().form_valid(form)
    # HU-074 | ESCENARIO 2 | A | Errores en formulario (formato inválido, tamaño excedido)


class ProductImageUpdateView(StaffPermissionRequiredMixin, UpdateView):
    """
    HU-075: Editar imagen de producto (texto alternativo)
    """
    model = ProductImage
    form_class = ProductImageUpdateForm
    template_name = TEMPLATE_PRODUCTIMAGE_FORM
    permission_required = 'products.change_productimage'  # HU-075 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_IMAGE_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_IMAGE_LIST
        context[CONTEXT_IS_UPDATE] = True
        return context
    
    def form_valid(self, form):
        # HU-075 | ESCENARIO 1 | H | Texto alternativo actualizado exitosamente
        messages.success(self.request, MSG_PRODUCT_IMAGE_UPDATED)
        return super().form_valid(form)
    # HU-075 | ESCENARIO 2 | A | Errores en formulario
    # HU-075 | ESCENARIO 4 | E | Imagen no existe → HTTP 404


class ProductImageDeleteView(StaffPermissionRequiredMixin, DeleteView):
    """
    HU-076: Eliminar imagen de producto
    """
    model = ProductImage
    form_class = ProductImageDeleteForm
    template_name = TEMPLATE_PRODUCTIMAGE_CONFIRM_DELETE
    permission_required = 'products.delete_productimage'  # HU-076 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_IMAGE_LIST)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['image'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        image = self.get_object()
        context[CONTEXT_OBJECT_NAME] = 'Imagen'
        context[CONTEXT_OBJECT_DISPLAY] = image.image.name.split('/')[-1]
        context[CONTEXT_CANCEL_URL] = PRODUCTS_IMAGE_LIST
        context[CONTEXT_IMAGE_PREVIEW] = image.image.url
        context['alt_text'] = image.alt_text
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.delete(request, *args, **kwargs)
        # HU-076 | ESCENARIO 2 | A | Cancelar eliminación
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        image_name = image.image.name.split('/')[-1]
        response = super().delete(request, *args, **kwargs)
        # HU-076 | ESCENARIO 1 | H | Imagen eliminada exitosamente
        messages.success(request, MSG_PRODUCT_IMAGE_DELETED.format(name=image_name))
        return response


# =============================================================================
# PRODUCT CRUD VIEWS (HU-009, HU-010, HU-011, HU-012, HU-013)
# =============================================================================

class ProductListView(StaffPermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """
    HU-009: Listar productos (admin)
    """
    model = Product
    template_name = TEMPLATE_PRODUCT_LIST
    context_object_name = CONTEXT_PRODUCTS
    permission_required = 'products.view_product'  # HU-009 | ESCENARIO 5 | E | Sin permisos
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (FILTER_NAME, FILTER_NAME, 'icontains'),
        (FILTER_CATEGORY, 'category__id', 'exact'),
        (FILTER_PRODUCT_TYPE, 'product_type', 'exact'),
        (FILTER_IS_ACTIVE, FILTER_IS_ACTIVE, 'exact'),
    ]
    
    def get_context_data(self, **kwargs):
        # HU-009 | ESCENARIO 1 | H | Lista cargada exitosamente con productos activos y archivados
        # HU-009 | ESCENARIO 2 | H | Búsqueda por nombre (filtro name)
        # HU-009 | ESCENARIO 3 | H | Filtro por estado (activo/archivado)
        # HU-009 | ESCENARIO 4 | A | Sin productos → template muestra mensaje y botón crear
        context = super().get_context_data(**kwargs)
        rows = []
        for product in context[CONTEXT_PRODUCTS]:
            featured_image = product.get_featured_image()
            
            if featured_image:
                image_html = mark_safe(f'<img src="{featured_image.image.url}" class="w-12 h-12 object-cover rounded-lg">')
            else:
                image_html = mark_safe(ICON_IMAGE_PLACEHOLDER)
            
            product_type_display = PRODUCT_TYPES_DISPLAY.get(product.product_type, product.product_type)
            badge_class = BADGE_CLASS_ACTIVE if product.is_active else BADGE_CLASS_INACTIVE
            badge_text = BADGE_TEXT_ACTIVE if product.is_active else BADGE_TEXT_INACTIVE
            
            rows.append({
                'pk': product.pk,
                'values': [
                    image_html,
                    product.name,
                    product.category.name if product.category else '—',
                    f'${product.price:,.0f}',
                    product_type_display,
                    mark_safe(f'<span class="px-2 py-1 text-xs rounded-full {badge_class}">{badge_text}</span>'),
                ],
            })
        
        context['rows'] = rows
        context['headers'] = HEADERS_PRODUCT
        context['categories'] = Category.objects.all()
        context['product_types'] = Product.PRODUCT_TYPES
        context['filters_config'] = [
            {'name': FILTER_NAME, 'label': HEADER_NAME, 'type': 'search', 'placeholder': UI_PLACEHOLDER_SEARCH_PRODUCT},
            {'name': FILTER_CATEGORY, 'label': HEADER_CATEGORY, 'type': 'select', 'options': [
                {'value': cat.id, 'label': cat.name} for cat in Category.objects.all()
            ]},
            {'name': FILTER_PRODUCT_TYPE, 'label': HEADER_TYPE, 'type': 'select', 'options': [
                {'value': PRODUCT_TYPE_FABRICA, 'label': PRODUCT_TYPES_DISPLAY[PRODUCT_TYPE_FABRICA]},
                {'value': PRODUCT_TYPE_COLECCION_LIMITADA, 'label': PRODUCT_TYPES_DISPLAY[PRODUCT_TYPE_COLECCION_LIMITADA]},
            ]},
            {'name': FILTER_IS_ACTIVE, 'label': UI_STATUS_LABEL, 'type': 'select', 'options': [
                {'value': ACTIVE_FILTER_VALUE, 'label': BADGE_TEXT_ACTIVE},
                {'value': INACTIVE_FILTER_VALUE, 'label': BADGE_TEXT_INACTIVE},
            ]},
        ]
        return context


class ProductCreateView(StaffPermissionRequiredMixin, CreateView):
    """
    HU-010: Crear producto
    """
    model = Product
    form_class = ProductCreateForm
    template_name = TEMPLATE_PRODUCT_FORM
    permission_required = 'products.add_product'  # HU-010 | ESCENARIO 4 | E | Sin permisos
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_LIST
        context[CONTEXT_IS_CREATE] = True
        return context
    
    def get_success_url(self):
        # HU-010 | ESCENARIO 1 | H | Redirige a edición del producto creado
        return reverse(PRODUCTS_EDIT, kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # HU-010 | ESCENARIO 1 | H | Producto creado exitosamente
        response = super().form_valid(form)
        messages.success(self.request, MSG_PRODUCT_CREATED.format(name=form.instance.name))
        return response
    # HU-010 | ESCENARIO 2 | A | Errores en formulario (manejado por CreateView)
    # HU-010 | ESCENARIO 3 | A | Nombre duplicado (validación en ProductCreateForm.clean_name)


class ProductUpdateView(StaffPermissionRequiredMixin, UpdateView):
    """
    HU-011: Editar producto
    """
    model = Product
    form_class = ProductUpdateForm
    template_name = TEMPLATE_PRODUCT_FORM
    permission_required = 'products.change_product'  # HU-011 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_LIST
        context[CONTEXT_IS_UPDATE] = True
        context[CONTEXT_PRODUCT_COLORS] = self.object.product_colors.filter(is_active=True)
        context[CONTEXT_VARIANTS] = self.object.variants.filter(is_active=True)
        return context
    
    def form_valid(self, form):
        # HU-011 | ESCENARIO 1 | H | Producto actualizado exitosamente
        response = super().form_valid(form)
        messages.success(self.request, MSG_PRODUCT_UPDATED.format(name=form.instance.name))
        return response
    # HU-011 | ESCENARIO 2 | A | Errores en formulario
    # HU-011 | ESCENARIO 3 | E | Producto no existe → HTTP 404


class ProductDeleteView(StaffPermissionRequiredMixin, DeleteView):
    """
    HU-012: Eliminar producto (soft delete)
    """
    model = Product
    form_class = ProductDeleteForm
    template_name = TEMPLATE_PRODUCT_CONFIRM_DELETE
    permission_required = 'products.delete_product'  # HU-012 | ESCENARIO 5 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_OBJECT_NAME] = 'Producto'
        context[CONTEXT_OBJECT_DISPLAY] = self.get_object().name
        context[CONTEXT_CANCEL_URL] = PRODUCTS_LIST
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.delete(request, *args, **kwargs)
        # HU-012 | ESCENARIO 3 | A | Cancelar eliminación
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        product_name = product.name
        # HU-012 | ESCENARIO 1 | H | Producto archivado (soft delete)
        product.soft_delete(user=request.user)
        messages.success(request, MSG_PRODUCT_DELETED.format(name=product_name))
        return redirect(self.success_url)
    # HU-012 | ESCENARIO 2 | A | Producto con pedidos asociados (validación en ProductDeleteForm)


class ProductRestoreView(StaffPermissionRequiredMixin, TemplateView):
    """
    HU-012 | ESCENARIO 4 | H | Restaurar producto desde papelera
    """
    model = Product
    form_class = ProductRestoreForm
    template_name = TEMPLATE_PRODUCT_RESTORE
    permission_required = 'products.change_product'
    success_url = reverse_lazy(PRODUCTS_TRASHCAN)
    
    def get_object(self):
        return get_object_or_404(Product.all_objects, pk=self.kwargs['pk'], is_active=False)
    
    def get_form(self):
        return self.form_class(product=self.get_object(), data=self.request.POST or None)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context[CONTEXT_PRODUCT] = product
        context['form'] = self.get_form()
        context[CONTEXT_CANCEL_URL] = PRODUCTS_TRASHCAN
        context[CONTEXT_OBJECT_NAME] = 'Producto'
        context[CONTEXT_OBJECT_DISPLAY] = product.name
        return context
    
    def post(self, request, *args, **kwargs):
        product = self.get_object()
        form = self.get_form()
        if form.is_valid():
            # HU-012 | ESCENARIO 4 | H | Producto restaurado exitosamente
            product.restore(user=request.user)
            messages.success(request, MSG_PRODUCT_RESTORED.format(name=product.name))
            return redirect(PRODUCTS_LIST)
        return self.render_to_response(self.get_context_data(form=form))


class ProductTrashcanView(StaffPermissionRequiredMixin, ListView):
    """
    HU-012 (parte): Ver papelera de productos
    """
    model = Product
    template_name = TEMPLATE_PRODUCT_TRASHCAN
    context_object_name = CONTEXT_PRODUCTS
    permission_required = 'products.view_product'
    paginate_by = PAGINATE_BY_DEFAULT
    
    def get_queryset(self):
        # HU-012 | ESCENARIO 1,2 | A | Productos archivados visibles en papelera
        return Product.all_objects.filter(is_active=False).order_by(ORDER_BY_DELETED_AT)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for product in context[CONTEXT_PRODUCTS]:
            rows.append({
                'pk': product.pk,
                'values': [
                    product.name,
                    product.category.name if product.category else '—',
                    f'${product.price:,.0f}',
                    product.deleted_at.strftime(DATE_FORMAT_DISPLAY) if product.deleted_at else '—',
                ],
            })
        context['rows'] = rows
        context['headers'] = HEADERS_PRODUCT_TRASHCAN
        return context


# =============================================================================
# PRODUCT COLOR CRUD VIEWS (HU-013: Gestionar tallas y stock - colores como parte de variantes)
# =============================================================================

class ProductColorCreateView(StaffPermissionRequiredMixin, CreateView):
    """
    HU-013 | ESCENARIO 1 | H | Asignar colores a un producto (parte de gestión de variantes)
    """
    model = ProductColor
    form_class = ProductColorCreateForm
    template_name = TEMPLATE_PRODUCTCOLOR_FORM
    permission_required = 'products.add_productcolor'  # HU-013 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def dispatch(self, request, *args, **kwargs):
        # HU-013 | ESCENARIO 1 | H | Obtiene el producto para asignar color
        self.product = get_object_or_404(Product, pk=kwargs['product_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs[CONTEXT_PRODUCT] = self.product
        return kwargs
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_PRODUCT] = self.product
        context[CONTEXT_CANCEL_URL] = PRODUCTS_EDIT
        context[CONTEXT_CANCEL_ARGS] = [self.product.pk]
        context[CONTEXT_TITLE] = f'Agregar Color a {self.product.name}'
        return context
    
    def form_valid(self, form):
        # HU-013 | ESCENARIO 1 | H | Color asignado al producto exitosamente
        form.instance.product = self.product
        return super().form_valid(form)
    # HU-013 | ESCENARIO 3 | E | Color ya existe para este producto (validación en form)


class ProductColorUpdateView(StaffPermissionRequiredMixin, UpdateView):
    """
    HU-013 | ESCENARIO 2 | H | Actualizar imágenes y orden de colores del producto
    """
    model = ProductColor
    form_class = ProductColorUpdateForm
    template_name = TEMPLATE_PRODUCTCOLOR_FORM
    permission_required = 'products.change_productcolor'  # HU-013 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_PRODUCT] = self.object.product
        context[CONTEXT_CANCEL_URL] = PRODUCTS_EDIT
        context[CONTEXT_CANCEL_ARGS] = [self.object.product.pk]
        context[CONTEXT_TITLE] = f'Editar Color - {self.object.color.name}'
        return context
    
    def form_valid(self, form):
        # HU-013 | ESCENARIO 2 | H | Configuración de color actualizada
        response = super().form_valid(form)
        messages.success(self.request, MSG_PRODUCT_COLOR_UPDATED.format(name=self.object.color.name))
        return redirect(PRODUCTS_EDIT, pk=self.object.product.pk)
    # HU-013 | ESCENARIO 2 | A | Imagen destacada no está en imágenes seleccionadas (validación en form)


class ProductColorDeleteView(StaffPermissionRequiredMixin, SortableDeleteMixin, DeleteView):
    """
    HU-013 | ESCENARIO 4 | A | Deshabilitar/eliminar un color del producto
    """
    model = ProductColor
    form_class = ProductColorDeleteForm
    template_name = TEMPLATE_PRODUCTCOLOR_CONFIRM_DELETE
    permission_required = 'products.delete_productcolor'  # HU-013 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product_color'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_color = self.get_object()
        context[CONTEXT_PRODUCT] = product_color.product
        context[CONTEXT_OBJECT_NAME] = 'Color del producto'
        context[CONTEXT_OBJECT_DISPLAY] = f'{product_color.color.name} para {product_color.product.name}'
        context[CONTEXT_CANCEL_URL] = PRODUCTS_EDIT
        context[CONTEXT_CANCEL_ARGS] = [product_color.product.pk]
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.delete(request, *args, **kwargs)
        # HU-013 | ESCENARIO 3 | A | Cancelar eliminación
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        product_color = self.get_object()
        product_pk = product_color.product.pk
        color_name = product_color.color.name
        # HU-013 | ESCENARIO 4 | A | Color eliminado/deshabilitado del producto
        product_color.delete()
        messages.success(request, MSG_PRODUCT_COLOR_DELETED.format(name=color_name))
        return redirect(PRODUCTS_EDIT, pk=product_pk)
    # HU-013 | ESCENARIO 4 | A | Color con variantes activas (validación en form, no permite eliminar)


# =============================================================================
# PRODUCT VARIANT CRUD VIEWS (HU-013: Gestionar tallas y stock)
# =============================================================================

class ProductVariantCreateView(StaffPermissionRequiredMixin, CreateView):
    """
    HU-013 | ESCENARIO 1 | H | Asignar tallas y stock a un producto (crear variante)
    """
    model = ProductVariant
    form_class = ProductVariantCreateForm
    template_name = TEMPLATE_PRODUCTVARIANT_FORM
    permission_required = 'products.add_productvariant'  # HU-013 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def dispatch(self, request, *args, **kwargs):
        # HU-013 | ESCENARIO 1 | H | Obtiene el producto para asignar variante
        self.product = get_object_or_404(Product, pk=kwargs['product_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs[CONTEXT_PRODUCT] = self.product
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        if not self.object:
            self.object = self.model(product=self.product)
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_PRODUCT] = self.product
        context[CONTEXT_CANCEL_URL] = PRODUCTS_EDIT
        context[CONTEXT_CANCEL_ARGS] = [self.product.pk]
        context[CONTEXT_TITLE] = f'Agregar Variante a {self.product.name}'
        return context
    
    def form_valid(self, form):
        form.instance.product = self.product
        variant_name = f'{form.instance.product_color.color.name} - {form.instance.size.name}'
        # HU-013 | ESCENARIO 1 | H | Variante creada exitosamente
        messages.success(self.request, MSG_VARIANT_CREATED.format(variant=variant_name))
        return redirect(PRODUCTS_EDIT, pk=self.product.pk)
    # HU-013 | ESCENARIO 3 | E | Variante ya existe (validación en form)
    # HU-013 | ESCENARIO 3 | E | ProductColor no pertenece al producto (validación en form)


class ProductVariantUpdateView(StaffPermissionRequiredMixin, UpdateView):
    """
    HU-013 | ESCENARIO 2 | H | Actualizar stock de una talla
    HU-013 | ESCENARIO 3 | E | Stock negativo no permitido
    """
    model = ProductVariant
    form_class = ProductVariantUpdateForm
    template_name = TEMPLATE_PRODUCTVARIANT_FORM
    permission_required = 'products.change_productvariant'  # HU-013 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_PRODUCT] = self.object.product
        context[CONTEXT_CANCEL_URL] = PRODUCTS_EDIT
        context[CONTEXT_CANCEL_ARGS] = [self.object.product.pk]
        context[CONTEXT_TITLE] = f'Editar Variante - {self.object.product_color.color.name} / {self.object.size.name}'
        return context
    
    def form_valid(self, form):
        # HU-013 | ESCENARIO 2 | H | Stock actualizado exitosamente
        response = super().form_valid(form)
        messages.success(self.request, MSG_VARIANT_UPDATED)
        return redirect(PRODUCTS_EDIT, pk=self.object.product.pk)
    # HU-013 | ESCENARIO 3 | E | Stock negativo (validación en form)
    # HU-013 | ESCENARIO 4 | E | Variante no existe → HTTP 404


class ProductVariantDeleteView(StaffPermissionRequiredMixin, DeleteView):
    """
    HU-013 | ESCENARIO 4 | A | Deshabilitar una talla (soft delete)
    """
    model = ProductVariant
    form_class = ProductVariantDeleteForm
    template_name = TEMPLATE_PRODUCTVARIANT_CONFIRM_DELETE
    permission_required = 'products.delete_productvariant'  # HU-013 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['variant'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        variant = self.get_object()
        context[CONTEXT_PRODUCT] = variant.product
        context[CONTEXT_OBJECT_NAME] = 'Variante'
        context[CONTEXT_OBJECT_DISPLAY] = f'{variant.product_color.color.name} - {variant.size.name}'
        context[CONTEXT_CANCEL_URL] = PRODUCTS_EDIT
        context[CONTEXT_CANCEL_ARGS] = [variant.product.pk]
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.delete(request, *args, **kwargs)
        # HU-013 | ESCENARIO 3 | A | Cancelar eliminación
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        variant = self.get_object()
        product_pk = variant.product.pk
        # HU-013 | ESCENARIO 4 | A | Variante deshabilitada (is_active=False)
        variant.soft_delete(user=request.user)
        messages.success(request, MSG_VARIANT_DELETED)
        return redirect(PRODUCTS_EDIT, pk=product_pk)
    # HU-013 | ESCENARIO 4 | A | Variante con pedidos pendientes (validación en form)


class ProductVariantRestoreView(StaffPermissionRequiredMixin, FormView):
    """
    HU-013 | ESCENARIO 4 | A | Restaurar variante deshabilitada
    """
    form_class = ProductVariantRestoreForm
    template_name = TEMPLATE_PRODUCTVARIANT_RESTORE
    permission_required = 'products.change_productvariant'  # HU-013 | ESCENARIO 4 | E | Sin permisos

    def dispatch(self, request, *args, **kwargs):
        self.variant = get_object_or_404(ProductVariant.all_objects, pk=kwargs['pk'], is_active=False)
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['variant'] = self.variant
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_PRODUCT] = self.variant.product
        context[CONTEXT_OBJECT_NAME] = 'Variante'
        context[CONTEXT_OBJECT_DISPLAY] = f'{self.variant.product_color.color.name} - {self.variant.size.name}'
        context[CONTEXT_CANCEL_URL] = PRODUCTS_EDIT
        context[CONTEXT_CANCEL_ARGS] = [self.variant.product.pk]
        return context
    
    def form_valid(self, form):
        # HU-013 | ESCENARIO 4 | A | Variante restaurada exitosamente
        self.variant.restore(user=self.request.user)
        messages.success(self.request, MSG_VARIANT_RESTORED)
        return redirect(PRODUCTS_EDIT, pk=self.variant.product.pk)
    
    def form_invalid(self, form):
        # HU-013 | ESCENARIO 3 | A | Restauración fallida (conflicto con variante existente)
        messages.error(self.request, MSG_VARIANT_RESTORE_ERROR)
        return self.render_to_response(self.get_context_data(form=form))


class ProductVariantTrashcanView(StaffPermissionRequiredMixin, ListView):
    """
    HU-013 (parte): Ver variantes deshabilitadas (papelera)
    """
    model = ProductVariant
    template_name = TEMPLATE_PRODUCTVARIANT_TRASHCAN
    context_object_name = CONTEXT_VARIANTS
    permission_required = 'products.view_productvariant'  # HU-013 | ESCENARIO 4 | E | Sin permisos

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs['product_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # HU-013 | ESCENARIO 4 | A | Lista de variantes deshabilitadas del producto
        return ProductVariant.all_objects.filter(
            product=self.product,
            is_active=False
        ).order_by(ORDER_BY_DELETED_AT)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_PRODUCT] = self.product
        return context


# =============================================================================
# COLLECTION CRUD VIEWS (HU-014, HU-015, HU-016, HU-017, HU-018)
# =============================================================================

class CollectionListView(StaffPermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """
    HU-014: Listar colecciones (admin)
    """
    model = Collection
    template_name = TEMPLATE_COLLECTIONS_LIST
    context_object_name = 'collections'
    permission_required = PERM_COLLECTION_VIEW  # HU-014 | ESCENARIO 4 | E | Sin permisos
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (FILTER_NAME, FILTER_NAME, 'icontains'),
        ('status', 'status', 'exact'),
        (FILTER_IS_ACTIVE, FILTER_IS_ACTIVE, 'exact'),
    ]
    
    def get_queryset(self):
        # HU-014 | ESCENARIO 1 | H | Lista de colecciones cargada (activas y archivadas)
        qs = super().get_queryset()
        qs = qs.prefetch_related('products')
        return qs
    
    def _get_cover_image_html(self, collection):
        if collection.cover_image:
            return mark_safe(f'<img src="{collection.cover_image.url}" class="w-12 h-12 object-cover rounded-lg shadow-sm">')
        return mark_safe(ICON_IMAGE_PLACEHOLDER)
    
    def _get_name_html(self, collection):
        return mark_safe(f'<div><strong>{collection.name}</strong><br><span class="text-xs text-gray-500">{collection.slug}</span></div>')
    
    def _get_status_badge_html(self, collection):
        status_map = {
            'publicada': ('bg-green-100 text-green-700', 'Publicada'),
            'borrador': ('bg-amber-100 text-amber-700', 'Borrador'),
        }
        if collection.status in status_map:
            badge_class, badge_text = status_map[collection.status]
            return mark_safe(f'<span class="px-2 py-1 text-xs rounded-full {badge_class}">{badge_text}</span>')
        return mark_safe('<span class="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">Archivada</span>')
    
    def _get_active_badge_html(self, collection):
        badge_class = BADGE_CLASS_ACTIVE if collection.is_active else BADGE_CLASS_INACTIVE
        badge_text = BADGE_TEXT_ACTIVE if collection.is_active else BADGE_TEXT_INACTIVE
        return mark_safe(f'<span class="px-2 py-1 text-xs rounded-full {badge_class}">{badge_text}</span>')
    
    def _get_dates_html(self, collection):
        start_date = collection.start_date.strftime(DATE_FORMAT_DAY_MONTH_YEAR) if collection.start_date else '-'
        end_date = collection.end_date.strftime(DATE_FORMAT_DAY_MONTH_YEAR) if collection.end_date else '-'
        return mark_safe(f'<div class="text-xs">{start_date}<br>{end_date}</div>')
    
    def _build_collection_row(self, collection):
        return {
            'pk': collection.pk,
            'values': [
                self._get_cover_image_html(collection),
                self._get_name_html(collection),
                collection.products.count(),
                self._get_status_badge_html(collection),
                self._get_active_badge_html(collection),
                self._get_dates_html(collection),
            ],
        }
    
    def _build_collection_rows(self, collections):
        """Construye todas las filas de la tabla."""
        return [self._build_collection_row(collection) for collection in collections]    
    
    def _get_filters_config(self):
        """Retorna la configuración de filtros para el template."""
        # HU-014 | ESCENARIO 2 | H | Filtro por estado (publicada/borrador/archivada)
        return [
            {'name': FILTER_NAME, 'label': 'Nombre', 'type': 'search', 'placeholder': 'Buscar colección...'},
            {'name': 'status', 'label': 'Estado', 'type': 'select', 'options': [
                {'value': 'publicada', 'label': 'Publicada'},
                {'value': 'borrador', 'label': 'Borrador'},
                {'value': 'archivada', 'label': 'Archivada'},
            ]},
            {'name': FILTER_IS_ACTIVE, 'label': 'Activo', 'type': 'select', 'options': [
                {'value': 'true', 'label': 'Activo'},
                {'value': 'false', 'label': 'Inactivo'},
            ]},
        ]
    
    def _get_bulk_actions_config(self):
        """Retorna la configuración de acciones masivas."""
        return [
            {
                'name': 'archive_expired',
                'label': 'Archivar expiradas',
                'icon': 'fa-archive',
                'class': 'bg-amber-100 text-amber-700 hover:bg-amber-200',
                'confirm': '¿Archivar todas las colecciones expiradas?',
                'message': 'Esta acción archivará todas las colecciones cuya fecha de fin ya pasó.',
                'type': 'warning'
            },
            {
                'name': 'publish_scheduled',
                'label': 'Publicar programadas',
                'icon': 'fa-calendar-check',
                'class': 'bg-green-100 text-green-700 hover:bg-green-200',
                'confirm': '¿Publicar todas las colecciones programadas?',
                'message': 'Esta acción publicará todas las colecciones cuya fecha de inicio ya llegó.',
                'type': 'info'
            },
        ]
        
    def _handle_archive_expired(self, request):
        """Maneja la acción de archivar colecciones expiradas."""
        call_command('archive_collections')
        messages.success(request, 'Colecciones expiradas archivadas correctamente.')
    
    def _handle_publish_scheduled(self, request):
        """Maneja la acción de publicar colecciones programadas."""
        call_command('publish_collections')
        messages.success(request, 'Colecciones programadas publicadas correctamente.')
    
    def _handle_archive_selected(self, request, selected_ids):
        """Maneja la acción de archivar colecciones seleccionadas."""
        if not selected_ids:
            messages.warning(request, 'No se seleccionó ninguna colección.')
            return
        
        count = 0
        for collection_id in selected_ids:
            try:
                collection = Collection.objects.get(pk=collection_id)
                if collection.status == 'publicada':
                    collection.status = 'archivada'
                    collection.save(update_fields=['status'])
                    collection.update_products_type()
                    count += 1
            except Collection.DoesNotExist:
                pass
        messages.success(request, f'{count} colección(es) archivada(s).')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # HU-014 | ESCENARIO 1 | H | Construcción de tabla de colecciones
        # HU-014 | ESCENARIO 3 | A | Sin colecciones → template muestra mensaje
        context['rows'] = self._build_collection_rows(context['collections'])
        context['headers'] = ['Portada', 'Nombre', 'Productos', 'Estado', 'Activo', 'Fechas']
        context['filters_config'] = self._get_filters_config()
        context['bulk_actions'] = self._get_bulk_actions_config()
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle bulk actions."""
        action = request.POST.get('bulk_action')
        selected_ids = request.POST.getlist('selected_ids')
        
        action_handlers = {
            'archive_expired': self._handle_archive_expired,
            'publish_scheduled': self._handle_publish_scheduled,
            'archive_selected': lambda req: self._handle_archive_selected(req, selected_ids),
        }
        
        if action in action_handlers:
            action_handlers[action](request)
        else:
            messages.error(request, 'Acción no válida.')
        
        return redirect(request.META.get('HTTP_REFERER', reverse('products:collection_list')))


class CollectionCreateView(StaffPermissionRequiredMixin, CreateView):
    """
    HU-015: Crear colección
    """
    model = Collection
    form_class = CollectionCreateForm
    template_name = TEMPLATE_COLLECTION_FORM
    permission_required = PERM_COLLECTION_ADD  # HU-015 | ESCENARIO 5 | E | Sin permisos
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_COLLECTION_LIST
        context[CONTEXT_IS_CREATE] = True
        return context
    
    def get_success_url(self):
        # HU-015 | ESCENARIO 1 | H | Redirige a edición de la colección creada
        return reverse(PRODUCTS_COLLECTION_EDIT, kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # HU-015 | ESCENARIO 1 | H | Colección creada exitosamente
        response = super().form_valid(form)
        messages.success(self.request, MSG_COLLECTION_CREATED.format(name=form.instance.name))
        return response
    # HU-015 | ESCENARIO 2 | E | Fechas inválidas (inicio > fin) - validación en form
    # HU-015 | ESCENARIO 3 | E | Nombre duplicado - validación en modelo/form
    # HU-015 | ESCENARIO 4 | H | Estilos visuales personalizados (campos en el formulario)


class CollectionUpdateView(StaffPermissionRequiredMixin, UpdateView):
    """
    HU-016: Editar colección
    HU-018: Asignar productos a colección
    """
    model = Collection
    form_class = CollectionUpdateForm
    template_name = TEMPLATE_COLLECTION_FORM
    permission_required = PERM_COLLECTION_CHANGE  # HU-016 | ESCENARIO 4 | E | Sin permisos
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_COLLECTION_LIST
        context[CONTEXT_IS_UPDATE] = True
        context['product_count'] = self.object.products.filter(is_active=True).count()
        return context
    
    def get_success_url(self):
        # HU-016 | ESCENARIO 1 | H | Redirige al listado
        return reverse(PRODUCTS_COLLECTION_LIST)
    
    def form_valid(self, form):
        # HU-016 | ESCENARIO 1 | H | Colección actualizada exitosamente
        response = super().form_valid(form)
        messages.success(self.request, MSG_COLLECTION_UPDATED.format(name=form.instance.name))
        return response
    # HU-016 | ESCENARIO 2 | A | Colección con productos asignados y fechas modificadas (advertencia opcional)
    # HU-016 | ESCENARIO 3 | A | Colección expirada (se muestra indicador en template)
    # HU-018 | ESCENARIO 1 | H | Asignar producto a colección (checkbox)
    # HU-018 | ESCENARIO 2 | H | Quitar producto de colección (desmarcar checkbox)
    # HU-018 | ESCENARIO 3 | H | Asignación múltiple (widget ProductCheckboxSelectWidget)
    # HU-018 | ESCENARIO 4 | A | Producto ya asignado a otra colección limitada (validación en modelo)


class CollectionDeleteView(StaffPermissionRequiredMixin, DeleteView):
    """
    HU-017: Eliminar colección (soft delete)
    """
    model = Collection
    form_class = CollectionDeleteForm
    template_name = TEMPLATE_COLLECTION_CONFIRM_DELETE
    permission_required = PERM_COLLECTION_DELETE  # HU-017 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_COLLECTION_LIST)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['collection'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection = self.get_object()
        context[CONTEXT_OBJECT_NAME] = 'Colección'
        context[CONTEXT_OBJECT_DISPLAY] = collection.name
        context[CONTEXT_CANCEL_URL] = PRODUCTS_COLLECTION_LIST
        context['product_count'] = collection.products.filter(is_active=True).count()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.delete(request, *args, **kwargs)
        # HU-017 | ESCENARIO 3 | A | Cancelar eliminación
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        collection = self.get_object()
        collection_name = collection.name
        # HU-017 | ESCENARIO 1 | H | Colección archivada exitosamente
        collection.soft_delete(user=request.user)
        messages.success(request, MSG_COLLECTION_DELETED.format(name=collection_name))
        return redirect(self.success_url)
    # HU-017 | ESCENARIO 2 | A | Colección con productos asignados (advertencia en template/form)


class CollectionRestoreView(StaffPermissionRequiredMixin, TemplateView):
    """
    HU-017 | ESCENARIO 3 | H | Restaurar colección
    """
    model = Collection
    form_class = CollectionRestoreForm
    template_name = TEMPLATE_COLLECTION_RESTORE
    permission_required = PERM_COLLECTION_CHANGE  # HU-017 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(PRODUCTS_COLLECTION_TRASHCAN)
    
    def get_object(self):
        return get_object_or_404(Collection.all_objects, pk=self.kwargs['pk'], is_active=False)
    
    def get_form(self):
        return self.form_class(collection=self.get_object(), data=self.request.POST or None)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection = self.get_object()
        context['collection'] = collection
        context['form'] = self.get_form()
        context[CONTEXT_CANCEL_URL] = PRODUCTS_COLLECTION_TRASHCAN
        context[CONTEXT_OBJECT_NAME] = 'Colección'
        context[CONTEXT_OBJECT_DISPLAY] = collection.name
        context['product_count'] = collection.products.filter(is_active=True).count()
        return context
    
    def post(self, request, *args, **kwargs):
        collection = self.get_object()
        form = self.get_form()
        if form.is_valid():
            # HU-017 | ESCENARIO 3 | H | Colección restaurada exitosamente
            collection.restore(user=request.user)
            
            if form.cleaned_data.get('restore_products_type'):
                collection.update_products_type()
            
            messages.success(request, MSG_COLLECTION_RESTORED.format(name=collection.name))
            return redirect(PRODUCTS_COLLECTION_LIST)
        return self.render_to_response(self.get_context_data(form=form))
    # HU-017 | ESCENARIO 3 | A | Conflicto al restaurar (slug duplicado) - validación en form


class CollectionTrashcanView(StaffPermissionRequiredMixin, ListView):
    """
    HU-017 (parte): Ver papelera de colecciones
    """
    model = Collection
    template_name = TEMPLATE_COLLECTION_TRASHCAN
    context_object_name = 'collections'
    permission_required = PERM_COLLECTION_VIEW  # HU-017 | ESCENARIO 4 | E | Sin permisos
    paginate_by = PAGINATE_BY_DEFAULT
    
    def get_queryset(self):
        # HU-017 | ESCENARIO 1,2 | A | Colecciones archivadas visibles en papelera
        return Collection.all_objects.filter(is_active=False).order_by(ORDER_BY_DELETED_AT)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        
        for collection in context['collections']:
            rows.append({
                'pk': collection.pk,
                'values': [
                    collection.name,
                    collection.products.count(),
                    collection.deleted_at.strftime(DATE_FORMAT_DISPLAY) if collection.deleted_at else '-',
                ],
            })
        
        context['rows'] = rows
        context['headers'] = ['Nombre', 'Productos', 'Eliminado el']
        
        return context


class CollectionStyleView(StaffPermissionRequiredMixin, UpdateView):
    """
    HU-016 (parte): Configuración de estilos de colección
    HU-015 | ESCENARIO 4 | H | Estilos visuales personalizados
    """
    model = Collection
    form_class = CollectionStyleForm
    template_name = TEMPLATE_COLLECTION_STYLE_FORM
    permission_required = PERM_COLLECTION_CHANGE  # HU-016 | ESCENARIO 4 | E | Sin permisos
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_COLLECTION_LIST
        context[CONTEXT_IS_UPDATE] = True
        context['collection'] = self.get_object()
        return context
    
    def get_success_url(self):
        return reverse(PRODUCTS_COLLECTION_LIST)
    
    def form_valid(self, form):
        # HU-015 | ESCENARIO 4 | H | Estilos visuales guardados exitosamente
        response = super().form_valid(form)
        messages.success(self.request, MSG_COLLECTION_STYLE_UPDATED.format(name=form.instance.name))
        return response