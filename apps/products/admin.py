from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.db import models as django_models
from .models import Size, Category, Color, Product, ProductVariant, Collection


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
    
    def product_count(self, obj):
        count = obj.products.count()
        return f"{count} productos"
    product_count.short_description = 'Productos'


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_preview', 'code', 'sort_order')
    list_editable = ('sort_order',)
    search_fields = ('name', 'code')
    ordering = ('sort_order',)
    list_per_page = 20
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Solo aplicar el widget al campo 'code'
        form.base_fields['code'].widget = admin.widgets.AdminTextInputWidget(
            attrs={'type': 'color', 'style': 'width: 80px; height: 35px; cursor: pointer;'}
        )
        return form
    
    def color_preview(self, obj):
        if obj.code:
            return format_html(
                '<div style="background-color: {}; width: 30px; height: 30px; border-radius: 5px; border: 1px solid #ccc;"></div>',
                obj.code
            )
        return "—"
    color_preview.short_description = 'Vista previa'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('size', 'color', 'stock', 'image_preview', 'image', 'is_portrait', 'is_active')
    exclude = ('sku',)
    readonly_fields = ('image_preview',)
    classes = ('collapse',)
    
    def image_preview(self, obj):
        if obj and obj.image and obj.image.url:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price_display', 'product_type', 'stock_display', 'is_active', 'created_at')
    list_filter = ('product_type', 'category', 'is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline]
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'total_stock')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'slug', 'description', 'category', 'price', 'product_type')
        }),
        ('Stock e inventario', {
            'fields': ('total_stock',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        return f"${obj.price:,.0f} COP"
    price_display.short_description = 'Precio'
    price_display.admin_order_field = 'price'
    
    def total_stock(self, obj):
        total = sum(v.stock for v in obj.variants.filter(is_active=True))
        return f"{total} unidades"
    total_stock.short_description = 'Stock total'
    
    def stock_display(self, obj):
        total = sum(v.stock for v in obj.variants.filter(is_active=True))
        if total == 0:
            return "Agotado"
        elif total < 5:
            return f"Bajo stock ({total})"
        return f"Disponible ({total})"
    stock_display.short_description = 'Stock'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product_link', 'size', 'color_preview', 'color', 'stock', 'is_portrait', 'is_active', 'updated_at')
    list_filter = ('size', 'color', 'is_active', 'is_portrait')
    search_fields = ('sku', 'product__name')
    list_editable = ('stock', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    exclude = ('sku',)
    list_per_page = 30
    list_select_related = ('product', 'size', 'color')
    
    fieldsets = (
        ('Información de la variante', {
            'fields': ('product', 'size', 'color', 'stock')
        }),
        ('Imagen', {
            'fields': ('image', 'is_portrait'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def product_link(self, obj):
        if obj and obj.product and obj.product.id:
            url = reverse('admin:products_product_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return "Sin producto"
    product_link.short_description = 'Producto'
    product_link.admin_order_field = 'product__name'
    
    def color_preview(self, obj):
        if obj and obj.color and obj.color.code:
            return format_html(
                '<div style="background-color: {}; width: 25px; height: 25px; border-radius: 4px; border: 1px solid #ccc;"></div>',
                obj.color.code
            )
        return "—"
    color_preview.short_description = 'Color'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        if not obj.sku:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            obj.sku = f"ZCD-{obj.product.id}-{obj.size.name}-{obj.color.name}-{timestamp}"
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'size', 'color')


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
    
    fieldsets = (
        ('Información de la colección', {
            'fields': ('name', 'slug', 'description', 'status', 'products')
        }),
        ('Fechas de vigencia', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',)
        }),
        ('Estilos visuales', {
            'fields': ('style_config',),
            'classes': ('collapse',),
        }),
        ('Auditoría', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def product_count(self, obj):
        count = obj.products.count()
        if count == 0:
            return "0 productos (vacía)"
        return f"{count} productos"
    product_count.short_description = 'Productos'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('products')