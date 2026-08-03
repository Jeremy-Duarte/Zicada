from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Size, Category, Color, Product, ProductVariant, Collection, ProductColor, ProductImage, InteractiveZone
from django.core.management import call_command
from django.contrib import messages


# =============================================================================
# CONSTANTES PARA ADMIN
# =============================================================================

# Strings duplicados
SECTION_AUDITORIA = 'Auditoría'
SECTION_IMAGENES = 'Imágenes'
SECTION_INFORMACION_BASICA = 'Información básica'
SECTION_STOCK = 'Stock e inventario'

# Estilos CSS duplicados
STYLE_COLOR_PICKER = 'width: 60px; height: 35px; cursor: pointer;'

# Etiquetas de sección
LABEL_COVER = '🎨 Imagen de portada'
LABEL_DATES = 'Fechas de vigencia'
LABEL_INFO = 'Información de la colección'


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'sort_order')
    list_editable = ('sort_order',)
    search_fields = ('name',)
    ordering = ('sort_order',)
    list_per_page = 20


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order', 'product_count')
    list_editable = ('sort_order',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    
    @admin.display(description='Productos')
    def product_count(self, obj):
        count = obj.products.count()
        return f"{count} productos"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image_preview', 'alt_text', 'created_at')
    list_display_links = ('id', 'image_preview')
    search_fields = ('alt_text',)
    list_per_page = 30
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Imagen', {
            'fields': ('image', 'alt_text')
        }),
        ('Información', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Vista previa')
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "Sin imagen"


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ('color', 'images_preview', 'featured_image', 'sort_order')
    readonly_fields = ('images_preview',)
    classes = ('collapse',)
    
    def images_preview(self, obj):
        sin_imagen = mark_safe('<span class="text-muted">Sin imágenes</span>')
        if not obj or not obj.pk:
            return sin_imagen
        
        if not obj.images.exists():
            return sin_imagen
        
        previews = []
        for img in obj.images.all()[:3]:
            if img.image and img.image.url:
                previews.append(f'<img src="{img.image.url}" width="30" height="30" style="object-fit: cover; margin-right: 5px;" />')
        
        if not previews:
            return sin_imagen
        
        return mark_safe(''.join(previews))


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_preview', 'code', 'sort_order')
    list_editable = ('sort_order',)
    search_fields = ('name', 'code')
    ordering = ('sort_order',)
    list_per_page = 20
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['code'].widget = admin.widgets.AdminTextInputWidget(
            attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}
        )
        return form
    
    @admin.display(description='Vista previa')
    def color_preview(self, obj):
        if obj.code:
            return format_html(
                '<div style="background-color: {}; width: 30px; height: 30px; border-radius: 5px; border: 1px solid #ccc;"></div>',
                obj.code
            )
        return "—"


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'sort_order', 'images_count', 'featured_image_preview')
    list_filter = ('color',)
    search_fields = ('product__name', 'color__name')
    list_editable = ('sort_order',)
    list_per_page = 30
    filter_horizontal = ('images',)
    
    fieldsets = (
        (SECTION_INFORMACION_BASICA, {
            'fields': ('product', 'color', 'sort_order')
        }),
        (SECTION_IMAGENES, {
            'fields': ('images', 'featured_image'),
            'description': 'Selecciona las imágenes para este color. La imagen destacada será la principal.'
        }),
    )
    
    @admin.display(description='Cantidad de imágenes')
    def images_count(self, obj):
        return obj.images.count()
    
    @admin.display(description='Imagen destacada')
    def featured_image_preview(self, obj):
        if obj.featured_image and obj.featured_image.image:
            return format_html('<img src="{}" width="40" height="40" style="object-fit: cover;" />', obj.featured_image.image.url)
        return "—"


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('product_color', 'size', 'stock', 'sku')
    readonly_fields = ('sku',)
    classes = ('collapse',)


class InteractiveZoneInline(admin.TabularInline):
    model = InteractiveZone
    extra = 0
    fields = ('product_color', 'x', 'y', 'width', 'height', 'label', 'sort_order')
    autocomplete_fields = ('product_color',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price_display', 'product_type', 'colors_count', 'stock_display', 'is_active', 'created_at')
    list_filter = ('product_type', 'category', 'is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductColorInline, ProductVariantInline]
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'total_stock')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (SECTION_INFORMACION_BASICA, {
            'fields': ('name', 'slug', 'description', 'category', 'price', 'product_type')
        }),
        (SECTION_STOCK, {
            'fields': ('total_stock',),
            'classes': ('collapse',)
        }),
        (SECTION_AUDITORIA, {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Precio', ordering='price')
    def price_display(self, obj):
        return f"${obj.price:,.0f} COP"
    
    @admin.display(description='Stock total')
    def total_stock(self, obj):
        total = sum(v.stock for v in obj.variants.filter(is_active=True))
        return f"{total} unidades"
    
    @admin.display(description='Stock')
    def stock_display(self, obj):
        total = sum(v.stock for v in obj.variants.filter(is_active=True))
        if total == 0:
            return "Agotado"
        elif total < 5:
            return f"Bajo stock ({total})"
        return f"Disponible ({total})"
    
    @admin.display(description='Colores')
    def colors_count(self, obj):
        return obj.product_colors.count()
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category').prefetch_related('product_colors', 'variants')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product_link', 'product_color', 'size', 'sku', 'stock', 'is_active', 'updated_at')
    list_filter = ('product_color__color', 'size', 'is_active')
    search_fields = ('sku', 'product__name')
    list_editable = ('stock', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    list_per_page = 30
    
    fieldsets = (
        ('Información de la variante', {
            'fields': ('product', 'product_color', 'size', 'stock')
        }),
        ('SKU', {
            'fields': ('sku',),
            'classes': ('collapse',)
        }),
        (SECTION_AUDITORIA, {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Producto', ordering='product__name')
    def product_link(self, obj):
        if obj and obj.product and obj.product.id:
            url = reverse('admin:products_product_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return "Sin producto"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        if not obj.sku:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            obj.sku = f"ZCD-{obj.product.id}-{obj.product_color.color.name}-{obj.size.name}-{timestamp}"
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'product_color', 'product_color__color', 'size')


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date', 'product_count', 'is_active')
    list_filter = ('status', 'is_active', 'start_date', 'end_date')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('products',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    list_per_page = 20
    date_hierarchy = 'created_at'
    inlines = [InteractiveZoneInline]
    
    def get_fieldsets(self, request, obj=None):
        """Construye los fieldsets dinámicamente para reducir complejidad cognitiva."""
        fieldsets = []
        fieldsets.extend(self._get_base_fieldsets(request, obj))
        return fieldsets
    
    def _get_base_fieldsets(self, request, obj=None):
        """Retorna los fieldsets base de la colección."""
        return [
            (LABEL_INFO, {
                'fields': ('name', 'slug', 'description', 'status', 'products')
            }),
            (LABEL_DATES, {
                'fields': ('start_date', 'end_date'),
                'classes': ('collapse',)
            }),
            (LABEL_COVER, {
                'fields': ('cover_image', 'interactive_background'),
                'description': 'Imagen que aparecerá en la tarjeta de la colección (recomendado: 800x600px)'
            }),
        ]
    
    @admin.display(description='Productos')
    def product_count(self, obj):
        count = obj.products.count()
        if count == 0:
            return "0 productos (vacía)"
        return f"{count} productos"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('products')
    
    actions = ['archive_expired_collections', 'publish_scheduled_collections', 'archive_selected_collections']
    
    @admin.action(description='Archivar colecciones expiradas')
    def archive_expired_collections(self, request, queryset):
        call_command('archive_collections')
        self.message_user(request, 'Colecciones expiradas archivadas correctamente.', messages.SUCCESS)
    
    @admin.action(description='Publicar colecciones programadas')
    def publish_scheduled_collections(self, request, queryset):
        call_command('publish_collections')
        self.message_user(request, 'Colecciones programadas publicadas correctamente.', messages.SUCCESS)
    
    @admin.action(description='Archivar colecciones seleccionadas')
    def archive_selected_collections(self, request, queryset):
        count = 0
        for collection in queryset:
            if collection.status == 'publicada':
                collection.status = 'archivada'
                collection.save()
                collection.update_products_type()
                count += 1
        self.message_user(request, f'{count} colección(es) archivada(s).')