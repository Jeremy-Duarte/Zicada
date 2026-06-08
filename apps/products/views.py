import re
import json
import csv
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Min, Max, Count
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
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
    TEMPLATE_COLLECTIONS_LIST,
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
    # Import Template Filenames
    IMPORT_TEMPLATE_FILENAME_SIZE,
    IMPORT_TEMPLATE_FILENAME_COLOR,
    IMPORT_TEMPLATE_FILENAME_CATEGORY,
    # Import Example Data
    IMPORT_EXAMPLE_DATA_SIZE,
    IMPORT_EXAMPLE_DATA_COLOR,
    IMPORT_EXAMPLE_DATA_CATEGORY,
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


class ProductCatalogView(PaginationMixin, FilterMixin, ListView):
    """Product catalog view with filters and pagination."""
    model = Product
    template_name = TEMPLATE_CATALOG
    context_object_name = CONTEXT_PRODUCTS
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (QUERY_PARAM_CATEGORY, 'category__slug', 'exact'),
        (QUERY_PARAM_PRODUCT_TYPE, 'product_type', 'exact'),
    ]
    
    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=PRODUCT_FILTER_ACTIVE)
        
        qs = qs.select_related('category').prefetch_related(
            'product_colors', 'product_colors__images', 'variants', 'variants__size'
        )
        
        # Search by name or description
        search = self.request.GET.get(QUERY_PARAM_SEARCH, '')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by price range
        min_price = self.request.GET.get(QUERY_PARAM_MIN_PRICE, '')
        max_price = self.request.GET.get(QUERY_PARAM_MAX_PRICE, '')
        
        if min_price and min_price.isdigit():
            qs = qs.filter(price__gte=int(min_price))
        
        if max_price and max_price.isdigit():
            qs = qs.filter(price__lte=int(max_price))
        
        # Ordering
        order_by = self.request.GET.get(QUERY_PARAM_ORDER_BY, ORDER_BY_CREATED_AT)
        allowed_orders = [choice[0] for choice in ORDER_CHOICES_CATALOG]
        if order_by in allowed_orders:
            qs = qs.order_by(order_by)
        else:
            qs = qs.order_by(ORDER_BY_CREATED_AT)
        
        return qs
    
    def get_context_data(self, **kwargs):
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


class CollectionListView(PaginationMixin, FilterMixin, ListView):
    """Collection list view with advanced filters."""
    model = Collection
    template_name = TEMPLATE_COLLECTIONS_LIST
    context_object_name = 'collections'
    paginate_by = PAGINATE_BY_COLLECTIONS
    
    filters = [
        (QUERY_PARAM_PRODUCT_TYPE, 'products__product_type', 'exact'),
    ]
    
    def get_queryset(self):
        # Apply simple filters from FilterMixin
        qs = super().get_queryset()
        
        # Base filters
        qs = qs.filter(is_active=True)
        
        # 1. Search by name (OR between two fields)
        search = self.request.GET.get(QUERY_PARAM_SEARCH, '')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # 2. Status filter
        status_filter = self.request.GET.get(QUERY_PARAM_STATUS, '')
        if status_filter == STATUS_FILTER_ACTIVE:
            qs = qs.filter(status=STATUS_PUBLISHED)
        elif status_filter == STATUS_FILTER_UPCOMING:
            qs = qs.filter(status=STATUS_DRAFT)
        elif status_filter == STATUS_FILTER_ARCHIVED:
            qs = qs.filter(status=STATUS_ARCHIVED)
        
        # 3. Price range filter
        min_price = self.request.GET.get(QUERY_PARAM_MIN_PRICE, '')
        max_price = self.request.GET.get(QUERY_PARAM_MAX_PRICE, '')
        
        if min_price and min_price.isdigit():
            qs = qs.filter(products__price__gte=int(min_price)).distinct()
        
        if max_price and max_price.isdigit():
            qs = qs.filter(products__price__lte=int(max_price)).distinct()
        
        # 4. Product count filter
        product_count_min = self.request.GET.get(QUERY_PARAM_PRODUCT_COUNT_MIN, '')
        product_count_max = self.request.GET.get(QUERY_PARAM_PRODUCT_COUNT_MAX, '')
        
        if product_count_min and product_count_min.isdigit():
            qs = qs.annotate(product_count=Count('products')).filter(product_count__gte=int(product_count_min))
        
        if product_count_max and product_count_max.isdigit():
            if not product_count_min:
                qs = qs.annotate(product_count=Count('products'))
            qs = qs.filter(product_count__lte=int(product_count_max))
        
        # 5. Date filter
        date_filter = self.request.GET.get(QUERY_PARAM_DATE_FILTER, '')
        now = timezone.now()
        
        if date_filter == DATE_FILTER_LAST_MONTH:
            qs = qs.filter(start_date__gte=now - timedelta(days=30))
        elif date_filter == DATE_FILTER_LAST_QUARTER:
            qs = qs.filter(start_date__gte=now - timedelta(days=90))
        elif date_filter == DATE_FILTER_LAST_SEMESTER:
            qs = qs.filter(start_date__gte=now - timedelta(days=180))
        elif date_filter == DATE_FILTER_LAST_YEAR:
            qs = qs.filter(start_date__gte=now - timedelta(days=365))
        elif date_filter == DATE_FILTER_UPCOMING:
            qs = qs.filter(start_date__gt=now, status=STATUS_DRAFT)
        
        # Ordering
        order_by = self.request.GET.get(QUERY_PARAM_ORDER_BY, ORDER_BY_CREATED_AT)
        allowed_orders = [choice[0] for choice in ORDER_CHOICES_COLLECTIONS]
        if order_by in allowed_orders:
            qs = qs.order_by(order_by)
        else:
            qs = qs.order_by(ORDER_BY_CREATED_AT)
        
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


class CollectionDetailView(PaginationMixin, FilterMixin, ListView):
    """Collection detail view with products."""
    model = Product
    template_name = TEMPLATE_COLLECTION_DETAIL
    context_object_name = CONTEXT_PRODUCTS
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (QUERY_PARAM_PRODUCT_TYPE, 'product_type', 'exact'),
    ]
    
    def dispatch(self, request, *args, **kwargs):
        self.collection = get_object_or_404(
            Collection, 
            slug=kwargs['slug'], 
            status=STATUS_PUBLISHED, 
            is_active=True
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=PRODUCT_FILTER_ACTIVE)
        qs = qs.filter(collections=self.collection)
        
        search = self.request.GET.get(QUERY_PARAM_SEARCH, '')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        min_price = self.request.GET.get(QUERY_PARAM_MIN_PRICE, '')
        max_price = self.request.GET.get(QUERY_PARAM_MAX_PRICE, '')
        
        if min_price and min_price.isdigit():
            qs = qs.filter(price__gte=int(min_price))
        
        if max_price and max_price.isdigit():
            qs = qs.filter(price__lte=int(max_price))
        
        order_by = self.request.GET.get(QUERY_PARAM_ORDER_BY, ORDER_BY_CREATED_AT)
        allowed_orders = [choice[0] for choice in ORDER_CHOICES_CATALOG]
        if order_by in allowed_orders:
            qs = qs.order_by(order_by)
        else:
            qs = qs.order_by(ORDER_BY_CREATED_AT)
        
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
        
        context['safe_custom_css'] = self._sanitize_css(self.collection.custom_css)
        
        return context


@require_GET
def product_detail(request, slug):
    """Display detailed product information."""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    product_colors = product.product_colors.filter(is_active=True).prefetch_related('images').order_by(ORDER_BY_SORT_ORDER)
    variants = product.variants.filter(is_active=True).select_related('product_color', 'size')
    
    # Build gallery images
    gallery_images = []
    for pc in product_colors:
        for img in pc.get_images():
            gallery_images.append({
                'image': img.image.url if img.image else '',
                'color_id': pc.color.id,
                'color_name': pc.color.name,
                'color_code': pc.color.code or '#cccccc',
                'is_featured': pc.featured_image == img,
            })
    
    # Build variants data
    variants_data = []
    for variant in variants:
        stock_display, stock_message = get_stock_display(variant.stock)
        
        variants_data.append({
            'id': variant.id,
            'color_id': variant.product_color.color.id,
            'color_name': variant.product_color.color.name,
            'color_code': variant.product_color.color.code or '#cccccc',
            'size_id': variant.size.id,
            'size_name': variant.size.name,
            'stock': variant.stock,
            'stock_display': stock_display,
            'stock_message': stock_message,
            'price': float(product.price),
            'image': variant.product_color.featured_image.image.url if variant.product_color.featured_image and variant.product_color.featured_image.image else '',
        })
    
    # Get unique colors
    unique_colors = []
    seen_color_ids = set()
    for variant in variants:
        color_id = variant.product_color.color.id
        if color_id not in seen_color_ids:
            seen_color_ids.add(color_id)
            unique_colors.append({
                'id': color_id,
                'name': variant.product_color.color.name,
                'code': variant.product_color.color.code or '#cccccc',
            })
    
    # Get unique sizes
    unique_sizes = []
    seen_size_ids = set()
    for variant in variants:
        size_id = variant.size.id
        if size_id not in seen_size_ids:
            seen_size_ids.add(size_id)
            unique_sizes.append({
                'id': size_id,
                'name': variant.size.name,
            })
    
    # Find featured image
    featured_image = None
    for img in gallery_images:
        if img.get('is_featured'):
            featured_image = img['image']
            break
    if not featured_image and gallery_images:
        featured_image = gallery_images[0]['image']
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).select_related('category').prefetch_related('product_colors', 'product_colors__images')[:PRODUCT_LIMIT_RELATED]
    
    context = {
        CONTEXT_PRODUCT: product,
        CONTEXT_VARIANTS: variants,
        'unique_colors': unique_colors,
        'unique_sizes': unique_sizes,
        'gallery_images': gallery_images,
        'gallery_images_json': json.dumps(gallery_images),
        'featured_image': featured_image,
        'variants_json': json.dumps(variants_data),
        'related_products': related_products,
    }
    return render(request, TEMPLATE_PRODUCT_DETAIL, context)


# =============================================================================
# SIZE CRUD VIEWS
# =============================================================================

class SizeListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """List sizes with filtering and pagination."""
    model = Size
    template_name = TEMPLATE_SIZE_LIST
    context_object_name = 'sizes'
    permission_required = 'products.view_size'
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (FILTER_NAME, FILTER_NAME, 'icontains'),
        ('sort_order', 'sort_order', 'exact'),
    ]

    def get_context_data(self, **kwargs):
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


class SizeCreateView(PermissionRequiredMixin, CreateView):
    """Create a new size."""
    model = Size
    form_class = SizeCreateForm
    template_name = TEMPLATE_SIZE_FORM
    permission_required = 'products.add_size'
    success_url = reverse_lazy(PRODUCTS_SIZE_LIST)
    
    def form_valid(self, form):
        messages.success(self.request, MSG_SIZE_CREATED.format(name=form.instance.name))
        return super().form_valid(form)


class SizeUpdateView(PermissionRequiredMixin, UpdateView):
    """Update an existing size."""
    model = Size
    form_class = SizeUpdateForm
    template_name = TEMPLATE_SIZE_FORM
    permission_required = 'products.change_size'
    success_url = reverse_lazy(PRODUCTS_SIZE_LIST)
    
    def form_valid(self, form):
        messages.success(self.request, MSG_SIZE_UPDATED.format(name=form.instance.name))
        return super().form_valid(form)


class SizeDeleteView(PermissionRequiredMixin, SortableDeleteMixin, DeleteView):
    """Delete a size."""
    model = Size
    form_class = SizeDeleteForm
    template_name = TEMPLATE_SIZE_CONFIRM_DELETE
    permission_required = 'products.delete_size'
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
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        size = self.get_object()
        size_name = size.name
        size.delete()
        messages.success(request, MSG_SIZE_DELETED.format(name=size_name))
        return redirect(self.success_url)


class SizeImportView(PermissionRequiredMixin, View):
    """Import sizes from CSV file."""
    permission_required = 'products.add_size'
    
    def get(self, request):
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
        
        if not file_obj:
            messages.error(request, MSG_IMPORT_NO_FILE)
            return redirect(PRODUCTS_SIZE_IMPORT)
        
        importer = SizeImporter(request, file_obj, update_existing=update_existing)
        results = importer.run()
        importer.add_messages()
        
        request.session['import_results'] = results
        
        return render(request, TEMPLATE_SIZE_IMPORT_RESULT, {'results': results})


@require_GET
def size_template(request):
    """Download size template CSV."""
    return generate_csv_response(
        filename=IMPORT_TEMPLATE_FILENAME_SIZE,
        headers=IMPORT_TEMPLATE_COLUMNS_SIZE,
        rows=IMPORT_EXAMPLE_DATA_SIZE
    )


# =============================================================================
# CATEGORY CRUD VIEWS
# =============================================================================

class CategoryListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """List categories with filtering and pagination."""
    model = Category
    template_name = TEMPLATE_CATEGORY_LIST
    context_object_name = 'categories'
    permission_required = 'products.view_category'
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (FILTER_NAME, FILTER_NAME, 'icontains'),
        ('slug', 'slug', 'icontains'),
        ('sort_order', 'sort_order', 'exact'),
    ]
    
    def get_context_data(self, **kwargs):
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


class CategoryCreateView(PermissionRequiredMixin, CreateView):
    """Create a new category."""
    model = Category
    form_class = CategoryCreateForm
    template_name = TEMPLATE_CATEGORY_FORM
    permission_required = 'products.add_category'
    success_url = reverse_lazy(PRODUCTS_CATEGORY_LIST)
    
    def form_valid(self, form):
        messages.success(self.request, MSG_CATEGORY_CREATED.format(name=form.instance.name))
        return super().form_valid(form)


class CategoryUpdateView(PermissionRequiredMixin, UpdateView):
    """Update an existing category."""
    model = Category
    form_class = CategoryUpdateForm
    template_name = TEMPLATE_CATEGORY_FORM
    permission_required = 'products.change_category'
    success_url = reverse_lazy(PRODUCTS_CATEGORY_LIST)
    
    def form_valid(self, form):
        messages.success(self.request, MSG_CATEGORY_UPDATED.format(name=form.instance.name))
        return super().form_valid(form)


class CategoryDeleteView(PermissionRequiredMixin, DeleteView):
    """Delete a category."""
    model = Category
    form_class = CategoryDeleteForm
    template_name = TEMPLATE_CATEGORY_CONFIRM_DELETE
    permission_required = 'products.delete_category'
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
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        category_name = category.name
        category.delete()
        messages.success(request, MSG_CATEGORY_DELETED.format(name=category_name))
        return redirect(self.success_url)


class CategoryImportView(PermissionRequiredMixin, View):
    """Import categories from CSV file."""
    permission_required = 'products.add_category'
    
    def get(self, request):
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
        
        if not file_obj:
            messages.error(request, MSG_IMPORT_NO_FILE)
            return redirect(PRODUCTS_CATEGORY_IMPORT)
        
        importer = CategoryImporter(request, file_obj, update_existing=update_existing)
        results = importer.run()
        importer.add_messages()
        
        context = {'results': results}
        return render(request, TEMPLATE_CATEGORY_IMPORT_RESULT, context)


@require_GET
def category_template(request):
    """Download category template CSV."""
    return generate_csv_response(
        filename=IMPORT_TEMPLATE_FILENAME_CATEGORY,
        headers=IMPORT_TEMPLATE_COLUMNS_CATEGORY,
        rows=IMPORT_EXAMPLE_DATA_CATEGORY
    )


# =============================================================================
# COLOR CRUD VIEWS
# =============================================================================

class ColorListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """List colors with filtering and pagination."""
    model = Color
    template_name = TEMPLATE_COLOR_LIST
    context_object_name = 'colors'
    permission_required = 'products.view_color'
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (FILTER_NAME, FILTER_NAME, 'icontains'),
        ('code', 'code', 'icontains'),
        ('sort_order', 'sort_order', 'exact'),
    ]
    
    def get_context_data(self, **kwargs):
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


class ColorCreateView(PermissionRequiredMixin, CreateView):
    """Create a new color."""
    model = Color
    form_class = ColorCreateForm
    template_name = TEMPLATE_COLOR_FORM
    permission_required = 'products.add_color'
    success_url = reverse_lazy(PRODUCTS_COLOR_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_COLOR_LIST
        return context
    
    def form_valid(self, form):
        messages.success(self.request, MSG_COLOR_CREATED.format(name=form.instance.name))
        return super().form_valid(form)


class ColorUpdateView(PermissionRequiredMixin, UpdateView):
    """Update an existing color."""
    model = Color
    form_class = ColorUpdateForm
    template_name = TEMPLATE_COLOR_FORM
    permission_required = 'products.change_color'
    success_url = reverse_lazy(PRODUCTS_COLOR_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_COLOR_LIST
        return context
    
    def form_valid(self, form):
        messages.success(self.request, MSG_COLOR_UPDATED.format(name=form.instance.name))
        return super().form_valid(form)


class ColorDeleteView(PermissionRequiredMixin, SortableDeleteMixin, DeleteView):
    """Delete a color."""
    model = Color
    form_class = ColorDeleteForm
    template_name = TEMPLATE_COLOR_CONFIRM_DELETE
    permission_required = 'products.delete_color'
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
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        color = self.get_object()
        color_name = color.name
        color.delete()
        messages.success(request, MSG_COLOR_DELETED.format(name=color_name))
        return redirect(self.success_url)


class ColorImportView(PermissionRequiredMixin, View):
    """Import colors from CSV file."""
    permission_required = 'products.add_color'
    
    def get(self, request):
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
        
        if not file_obj:
            messages.error(request, MSG_IMPORT_NO_FILE)
            return redirect(PRODUCTS_COLOR_IMPORT)
        
        importer = ColorImporter(request, file_obj, update_existing=update_existing)
        results = importer.run()
        importer.add_messages()
        
        context = {'results': results}
        return render(request, TEMPLATE_COLOR_IMPORT_RESULT, context)


@require_GET
def color_template(request):
    """Download color template CSV."""
    return generate_csv_response(
        filename=IMPORT_TEMPLATE_FILENAME_COLOR,
        headers=IMPORT_TEMPLATE_COLUMNS_COLOR,
        rows=IMPORT_EXAMPLE_DATA_COLOR
    )


# =============================================================================
# PRODUCT IMAGE CRUD VIEWS
# =============================================================================

class ProductImageListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """List product images with filtering and pagination."""
    model = ProductImage
    template_name = TEMPLATE_PRODUCTIMAGE_LIST
    context_object_name = 'images'
    permission_required = 'products.view_productimage'
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        ('alt_text', 'alt_text', 'icontains'),
        ('created_at', 'created_at', 'date'),
    ]
    
    def get_context_data(self, **kwargs):
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


class ProductImageCreateView(PermissionRequiredMixin, CreateView):
    """Upload a new product image."""
    model = ProductImage
    form_class = ProductImageCreateForm
    template_name = TEMPLATE_PRODUCTIMAGE_FORM
    permission_required = 'products.add_productimage'
    success_url = reverse_lazy(PRODUCTS_IMAGE_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_IMAGE_LIST
        return context
    
    def form_valid(self, form):
        image_name = form.instance.image.name.split('/')[-1]
        messages.success(self.request, MSG_PRODUCT_IMAGE_UPLOADED.format(name=image_name))
        return super().form_valid(form)


class ProductImageUpdateView(PermissionRequiredMixin, UpdateView):
    """Update product image alt text."""
    model = ProductImage
    form_class = ProductImageUpdateForm
    template_name = TEMPLATE_PRODUCTIMAGE_FORM
    permission_required = 'products.change_productimage'
    success_url = reverse_lazy(PRODUCTS_IMAGE_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_IMAGE_LIST
        context[CONTEXT_IS_UPDATE] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_PRODUCT_IMAGE_UPDATED)
        return super().form_valid(form)


class ProductImageDeleteView(PermissionRequiredMixin, DeleteView):
    """Delete a product image."""
    model = ProductImage
    form_class = ProductImageDeleteForm
    template_name = TEMPLATE_PRODUCTIMAGE_CONFIRM_DELETE
    permission_required = 'products.delete_productimage'
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
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        image_name = image.image.name.split('/')[-1]
        response = super().delete(request, *args, **kwargs)
        messages.success(request, MSG_PRODUCT_IMAGE_DELETED.format(name=image_name))
        return response


# =============================================================================
# PRODUCT CRUD VIEWS
# =============================================================================

class ProductListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """List products with filtering and pagination."""
    model = Product
    template_name = TEMPLATE_PRODUCT_LIST
    context_object_name = CONTEXT_PRODUCTS
    permission_required = 'products.view_product'
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (FILTER_NAME, FILTER_NAME, 'icontains'),
        (FILTER_CATEGORY, 'category__id', 'exact'),
        (FILTER_PRODUCT_TYPE, 'product_type', 'exact'),
        (FILTER_IS_ACTIVE, FILTER_IS_ACTIVE, 'exact'),
    ]
    
    def get_context_data(self, **kwargs):
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


class ProductCreateView(PermissionRequiredMixin, CreateView):
    """Create a new product."""
    model = Product
    form_class = ProductCreateForm
    template_name = TEMPLATE_PRODUCT_FORM
    permission_required = 'products.add_product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_LIST
        context[CONTEXT_IS_CREATE] = True
        return context
    
    def get_success_url(self):
        return reverse(PRODUCTS_EDIT, kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_PRODUCT_CREATED.format(name=form.instance.name))
        return response


class ProductUpdateView(PermissionRequiredMixin, UpdateView):
    """Update an existing product."""
    model = Product
    form_class = ProductUpdateForm
    template_name = TEMPLATE_PRODUCT_FORM
    permission_required = 'products.change_product'
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = PRODUCTS_LIST
        context[CONTEXT_IS_UPDATE] = True
        context[CONTEXT_PRODUCT_COLORS] = self.object.product_colors.filter(is_active=True)
        context[CONTEXT_VARIANTS] = self.object.variants.filter(is_active=True)
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_PRODUCT_UPDATED.format(name=form.instance.name))
        return response


class ProductDeleteView(PermissionRequiredMixin, DeleteView):
    """Soft-delete a product (move to trash)."""
    model = Product
    form_class = ProductDeleteForm
    template_name = TEMPLATE_PRODUCT_CONFIRM_DELETE
    permission_required = 'products.delete_product'
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
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        product_name = product.name
        product.soft_delete(user=request.user)
        messages.success(request, MSG_PRODUCT_DELETED.format(name=product_name))
        return redirect(self.success_url)


class ProductRestoreView(PermissionRequiredMixin, TemplateView):
    """Restore a product from trash."""
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
            product.restore(user=request.user)
            messages.success(request, MSG_PRODUCT_RESTORED.format(name=product.name))
            return redirect(PRODUCTS_LIST)
        return self.render_to_response(self.get_context_data(form=form))


class ProductTrashcanView(PermissionRequiredMixin, ListView):
    """View deleted products (trash can)."""
    model = Product
    template_name = TEMPLATE_PRODUCT_TRASHCAN
    context_object_name = CONTEXT_PRODUCTS
    permission_required = 'products.view_product'
    paginate_by = PAGINATE_BY_DEFAULT
    
    def get_queryset(self):
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
# PRODUCT COLOR CRUD VIEWS
# =============================================================================

class ProductColorCreateView(PermissionRequiredMixin, CreateView):
    """Add a color to a product."""
    model = ProductColor
    form_class = ProductColorCreateForm
    template_name = TEMPLATE_PRODUCTCOLOR_FORM
    permission_required = 'products.add_productcolor'
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def dispatch(self, request, *args, **kwargs):
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
        form.instance.product = self.product
        return super().form_valid(form)


class ProductColorUpdateView(PermissionRequiredMixin, UpdateView):
    """Update a product's color."""
    model = ProductColor
    form_class = ProductColorUpdateForm
    template_name = TEMPLATE_PRODUCTCOLOR_FORM
    permission_required = 'products.change_productcolor'
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_PRODUCT] = self.object.product
        context[CONTEXT_CANCEL_URL] = PRODUCTS_EDIT
        context[CONTEXT_CANCEL_ARGS] = [self.object.product.pk]
        context[CONTEXT_TITLE] = f'Editar Color - {self.object.color.name}'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_PRODUCT_COLOR_UPDATED.format(name=self.object.color.name))
        return redirect(PRODUCTS_EDIT, pk=self.object.product.pk)


class ProductColorDeleteView(PermissionRequiredMixin, SortableDeleteMixin, DeleteView):
    """Remove a color from a product."""
    model = ProductColor
    form_class = ProductColorDeleteForm
    template_name = TEMPLATE_PRODUCTCOLOR_CONFIRM_DELETE
    permission_required = 'products.delete_productcolor'
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
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        product_color = self.get_object()
        product_pk = product_color.product.pk
        color_name = product_color.color.name
        product_color.delete()
        messages.success(request, MSG_PRODUCT_COLOR_DELETED.format(name=color_name))
        return redirect(PRODUCTS_EDIT, pk=product_pk)


# =============================================================================
# PRODUCT VARIANT CRUD VIEWS
# =============================================================================

class ProductVariantCreateView(PermissionRequiredMixin, CreateView):
    """Create a new product variant."""
    model = ProductVariant
    form_class = ProductVariantCreateForm
    template_name = TEMPLATE_PRODUCTVARIANT_FORM
    permission_required = 'products.add_productvariant'
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def dispatch(self, request, *args, **kwargs):
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
        messages.success(self.request, MSG_VARIANT_CREATED.format(variant=variant_name))
        return redirect(PRODUCTS_EDIT, pk=self.product.pk)


class ProductVariantUpdateView(PermissionRequiredMixin, UpdateView):
    """Update an existing product variant."""
    model = ProductVariant
    form_class = ProductVariantUpdateForm
    template_name = TEMPLATE_PRODUCTVARIANT_FORM
    permission_required = 'products.change_productvariant'
    success_url = reverse_lazy(PRODUCTS_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_PRODUCT] = self.object.product
        context[CONTEXT_CANCEL_URL] = PRODUCTS_EDIT
        context[CONTEXT_CANCEL_ARGS] = [self.object.product.pk]
        context[CONTEXT_TITLE] = f'Editar Variante - {self.object.product_color.color.name} / {self.object.size.name}'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_VARIANT_UPDATED)
        return redirect(PRODUCTS_EDIT, pk=self.object.product.pk)


class ProductVariantDeleteView(PermissionRequiredMixin, DeleteView):
    """Soft-delete a product variant."""
    model = ProductVariant
    form_class = ProductVariantDeleteForm
    template_name = TEMPLATE_PRODUCTVARIANT_CONFIRM_DELETE
    permission_required = 'products.delete_productvariant'
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
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        variant = self.get_object()
        product_pk = variant.product.pk
        variant.soft_delete(user=request.user)
        messages.success(request, MSG_VARIANT_DELETED)
        return redirect(PRODUCTS_EDIT, pk=product_pk)


class ProductVariantRestoreView(PermissionRequiredMixin, FormView):
    """Restore a soft-deleted variant."""
    form_class = ProductVariantRestoreForm
    template_name = TEMPLATE_PRODUCTVARIANT_RESTORE
    permission_required = 'products.change_productvariant'

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
        self.variant.restore(user=self.request.user)
        messages.success(self.request, MSG_VARIANT_RESTORED)
        return redirect(PRODUCTS_EDIT, pk=self.variant.product.pk)
    
    def form_invalid(self, form):
        messages.error(self.request, MSG_VARIANT_RESTORE_ERROR)
        return self.render_to_response(self.get_context_data(form=form))


class ProductVariantTrashcanView(PermissionRequiredMixin, ListView):
    """View soft-deleted variants for a product."""
    model = ProductVariant
    template_name = TEMPLATE_PRODUCTVARIANT_TRASHCAN
    context_object_name = CONTEXT_VARIANTS
    permission_required = 'products.view_productvariant'

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs['product_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return ProductVariant.all_objects.filter(
            product=self.product,
            is_active=False
        ).order_by(ORDER_BY_DELETED_AT)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_PRODUCT] = self.product
        return context