from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, ProductVariant, ProductColor, ProductImage, Collection, Category, Size, Color
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import PermissionRequiredMixin
from apps.core.crud.mixins import PaginationMixin, FilterMixin
from .forms import SizeCreateForm, SizeDeleteForm, SizeUpdateForm, CategoryCreateForm, CategoryDeleteForm, CategoryUpdateForm, ColorCreateForm, ColorDeleteForm, ColorUpdateForm, ProductImageCreateForm, ProductImageUpdateForm, ProductImageDeleteForm, ProductUpdateForm, ProductDeleteForm, ProductCreateForm, ProductRestoreForm, ProductColorCreateForm, ProductColorUpdateForm, ProductColorDeleteForm, ProductVariantCreateForm, ProductVariantDeleteForm, ProductVariantRestoreForm, ProductVariantUpdateForm
from django.utils.safestring import mark_safe
import json

@staff_member_required
def stock_dashboard(request):
    low_stock_variants = ProductVariant.objects.low_stock().select_related('product', 'product_color__color', 'size')
    out_of_stock_variants = ProductVariant.objects.out_of_stock().select_related('product', 'product_color__color', 'size')
    products_with_stock = Product.objects.filter(
        variants__is_active=True,
        variants__stock__gt=0
    ).distinct()
    all_products = Product.objects.filter(is_active=True)
    out_of_stock_products = all_products.exclude(id__in=products_with_stock)
    
    product_stock_summary = []
    for product in all_products[:20]:
        total = product.total_stock()
        if total > 0:
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
    return render(request, 'products/stock_dashboard.html', context)

def catalog(request):
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related(
        'product_colors', 'product_colors__images', 'variants', 'variants__size'
    )
    categories = Category.objects.all().order_by('sort_order')
    
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    context = {
        'products': products,
        'categories': categories,
        'current_category': category_slug,
    }
    return render(request, 'products/catalog.html', context)

def collections_list(request):
    collections = Collection.objects.filter(
        status='publicada',
        is_active=True
    ).order_by('-created_at')
    
    context = {
        'collections': collections,
        'now': timezone.now(),
    }
    return render(request, 'products/collections_list.html', context)

def collection_detail(request, slug):
    collection = get_object_or_404(Collection, slug=slug, status='publicada', is_active=True)
    products = collection.products.filter(is_active=True).prefetch_related(
        'product_colors', 'product_colors__images', 'variants', 'variants__size'
    )
    
    context = {
        'collection': collection,
        'products': products,
    }
    return render(request, 'products/collection_detail.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    product_colors = product.product_colors.filter(is_active=True).prefetch_related('images').order_by('sort_order')
    
    variants = product.variants.filter(is_active=True).select_related('product_color', 'size')
    
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
    
    variants_data = []
    for variant in variants:
        stock = variant.stock
        if stock == 0:
            stock_display = 'out_of_stock'
            stock_message = 'Agotado'
        elif stock <= 10:
            stock_display = 'low_stock'
            stock_message = f'¡Últimas {stock} unidades!'
        else:
            stock_display = 'available'
            stock_message = 'Disponible'
        
        variants_data.append({
            'id': variant.id,
            'color_id': variant.product_color.color.id,
            'color_name': variant.product_color.color.name,
            'color_code': variant.product_color.color.code or '#cccccc',
            'size_id': variant.size.id,
            'size_name': variant.size.name,
            'stock': stock,
            'stock_display': stock_display,
            'stock_message': stock_message,
            'price': float(product.price),
            'image': variant.product_color.featured_image.image.url if variant.product_color.featured_image and variant.product_color.featured_image.image else '',
        })
    
    unique_colors = []
    seen_color_ids = set()
    for variant in variants:
        if variant.product_color.color.id not in seen_color_ids:
            seen_color_ids.add(variant.product_color.color.id)
            unique_colors.append({
                'id': variant.product_color.color.id,
                'name': variant.product_color.color.name,
                'code': variant.product_color.color.code or '#cccccc',
            })
    
    unique_sizes = []
    seen_size_ids = set()
    for variant in variants:
        if variant.size.id not in seen_size_ids:
            seen_size_ids.add(variant.size.id)
            unique_sizes.append({
                'id': variant.size.id,
                'name': variant.size.name,
            })
    
    featured_image = None
    for img in gallery_images:
        if img.get('is_featured'):
            featured_image = img['image']
            break
    if not featured_image and gallery_images:
        featured_image = gallery_images[0]['image']
    
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).select_related('category').prefetch_related('product_colors', 'product_colors__images')[:4]
    
    context = {
        'product': product,
        'variants': variants,
        'unique_colors': unique_colors,
        'unique_sizes': unique_sizes,
        'gallery_images': gallery_images,
        'gallery_images_json': json.dumps(gallery_images),
        'featured_image': featured_image,
        'variants_json': json.dumps(variants_data),
        'related_products': related_products,
    }
    return render(request, 'products/product_detail.html', context)

def products_list(request):
    pass #TODO

def product_detail(request):
    pass #TODO

class SizeListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    model = Size
    template_name = 'backoffice/size/size_list.html'
    context_object_name = 'sizes'
    permission_required = 'products.view_size'
    paginate_by = 20
    
    filters = [
        ('name', 'name', 'icontains'),
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
        context['headers'] = ['Nombre', 'Orden'] 
        return context


class SizeCreateView(PermissionRequiredMixin, CreateView):
    model = Size
    form_class = SizeCreateForm
    template_name = 'backoffice/size/size_form.html'
    permission_required = 'products.add_size'
    success_url = reverse_lazy('products:size_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Talla "{form.instance.name}" creada exitosamente.')
        return super().form_valid(form)


class SizeUpdateView(PermissionRequiredMixin, UpdateView):
    model = Size
    form_class = SizeUpdateForm
    template_name = 'backoffice/size/size_form.html'
    permission_required = 'products.change_size'
    success_url = reverse_lazy('products:size_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Talla "{form.instance.name}" actualizada exitosamente.')
        return super().form_valid(form)


class SizeDeleteView(PermissionRequiredMixin, DeleteView):
    model = Size
    form_class = SizeDeleteForm
    template_name = 'backoffice/size/size_confirm_delete.html'
    permission_required = 'products.delete_size'
    success_url = reverse_lazy('products:size_list')
    
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
        messages.success(request, f'Talla "{size_name}" eliminada exitosamente.')
        return redirect(self.success_url)


class CategoryListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    model = Category
    template_name = 'backoffice/category/category_list.html'
    context_object_name = 'categories'
    permission_required = 'products.view_category'
    paginate_by = 20
    
    filters = [
        ('name', 'name', 'icontains'),
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
        context['headers'] = ['Nombre', 'Slug', 'Orden']
        return context


class CategoryCreateView(PermissionRequiredMixin, CreateView):
    model = Category
    form_class = CategoryCreateForm
    template_name = 'backoffice/category/category_form.html'
    permission_required = 'products.add_category'
    success_url = reverse_lazy('products:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.instance.name}" creada exitosamente.')
        return super().form_valid(form)


class CategoryUpdateView(PermissionRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryUpdateForm
    template_name = 'backoffice/category/category_form.html'
    permission_required = 'products.change_category'
    success_url = reverse_lazy('products:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.instance.name}" actualizada exitosamente.')
        return super().form_valid(form)


class CategoryDeleteView(PermissionRequiredMixin, DeleteView):
    model = Category
    form_class = CategoryDeleteForm
    template_name = 'backoffice/category/category_confirm_delete.html'
    permission_required = 'products.delete_category'
    success_url = reverse_lazy('products:category_list')
    
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
        messages.success(request, f'Categoría "{category_name}" eliminada exitosamente.')
        return redirect(self.success_url)
    
class ColorListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    model = Color
    template_name = 'backoffice/color/color_list.html'
    context_object_name = 'colors'
    permission_required = 'products.view_color'
    paginate_by = 20
    
    filters = [
        ('name', 'name', 'icontains'),
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
        context['headers'] = ['Nombre', 'Código', 'Orden']
        
        return context


class ColorCreateView(PermissionRequiredMixin, CreateView):
    model = Color
    form_class = ColorCreateForm
    template_name = 'backoffice/color/color_form.html'
    permission_required = 'products.add_color'
    success_url = reverse_lazy('products:color_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = 'products:color_list'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Color "{form.instance.name}" creado exitosamente.')
        return super().form_valid(form)


class ColorUpdateView(PermissionRequiredMixin, UpdateView):
    model = Color
    form_class = ColorUpdateForm
    template_name = 'backoffice/color/color_form.html'
    permission_required = 'products.change_color'
    success_url = reverse_lazy('products:color_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = 'products:color_list'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Color "{form.instance.name}" actualizado exitosamente.')
        return super().form_valid(form)


class ColorDeleteView(PermissionRequiredMixin, DeleteView):
    model = Color
    form_class = ColorDeleteForm
    template_name = 'backoffice/color/color_confirm_delete.html'
    permission_required = 'products.delete_color'
    success_url = reverse_lazy('products:color_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['color'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'Color'
        context['object_display'] = self.get_object().name
        context['cancel_url'] = 'products:color_list'
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
        messages.success(request, f'Color "{color_name}" eliminado exitosamente.')
        return redirect(self.success_url)


class ProductImageListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    model = ProductImage
    template_name = 'backoffice/productimage/productimage_list.html'
    context_object_name = 'images'
    permission_required = 'products.view_productimage'
    paginate_by = 20
    
    filters = [
        ('alt_text', 'alt_text', 'icontains'),
        ('created_at', 'created_at', 'date'),
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for img in context['images']:
            rows.append({
                'pk': img.pk,
                'values': [
                    mark_safe(f'<img src="{img.image.url}" class="w-16 h-16 object-cover rounded-lg">'),
                    img.alt_text or '—',
                    img.created_at.strftime('%d/%m/%Y %H:%M'),
                ],
            })
        context['rows'] = rows
        context['headers'] = ['Imagen', 'Texto alternativo', 'Subida']
        return context


class ProductImageCreateView(PermissionRequiredMixin, CreateView):
    model = ProductImage
    form_class = ProductImageCreateForm
    template_name = 'backoffice/productimage/productimage_form.html'
    permission_required = 'products.add_productimage'
    success_url = reverse_lazy('products:productimage_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = 'products:productimage_list'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Imagen "{form.instance.image.name}" subida exitosamente.')
        return super().form_valid(form)


class ProductImageUpdateView(PermissionRequiredMixin, UpdateView):
    model = ProductImage
    form_class = ProductImageUpdateForm
    template_name = 'backoffice/productimage/productimage_form.html'
    permission_required = 'products.change_productimage'
    success_url = reverse_lazy('products:productimage_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = 'products:productimage_list'
        context['is_update'] = True
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Texto alternativo de la imagen actualizado exitosamente.')
        return super().form_valid(form)


class ProductImageDeleteView(PermissionRequiredMixin, DeleteView):
    model = ProductImage
    form_class = ProductImageDeleteForm
    template_name = 'backoffice/productimage/productimage_confirm_delete.html'
    permission_required = 'products.delete_productimage'
    success_url = reverse_lazy('products:productimage_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['image'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'Imagen'
        context['object_display'] = self.get_object().image.name.split('/')[-1]
        context['cancel_url'] = 'products:productimage_list'
        context['image_preview'] = self.get_object().image.url
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
        messages.success(request, f'Imagen "{image_name}" eliminada exitosamente.')
        return response

class ProductListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    model = Product
    template_name = 'backoffice/product/product_list.html'
    context_object_name = 'products'
    permission_required = 'products.view_product'
    paginate_by = 20
    
    filters = [
        ('name', 'name', 'icontains'),
        ('category', 'category__id', 'exact'),
        ('product_type', 'product_type', 'exact'),
        ('is_active', 'is_active', 'exact'),
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for product in context['products']:
            featured_image = product.get_featured_image()
            
            if featured_image:
                image_html = mark_safe(
                    f'<img src="{featured_image.image.url}" class="w-12 h-12 object-cover rounded-lg">'
                )
            else:
                image_html = mark_safe(
                    '<div class="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center text-gray-400">'
                    '<i class="fas fa-image"></i>'
                    '</div>'
                )
            
            product_type_display = dict(Product.PRODUCT_TYPES).get(product.product_type, product.product_type)
            
            rows.append({
                'pk': product.pk,
                'values': [
                    image_html,
                    product.name,
                    product.category.name if product.category else '—',
                    f'${product.price:,.0f}',
                    product_type_display,
                    mark_safe(
                        f'<span class="px-2 py-1 text-xs rounded-full {"bg-green-100 text-green-700" if product.is_active else "bg-red-100 text-red-700"}">'
                        f'{"Activo" if product.is_active else "Inactivo"}'
                        f'</span>'
                    ),
                ],
            })
        context['rows'] = rows
        context['headers'] = ['Imagen', 'Nombre', 'Categoría', 'Precio', 'Tipo', 'Estado']
        context['categories'] = Category.objects.all()
        
        context['product_types'] = Product.PRODUCT_TYPES
        
        context['filters_config'] = [
            {'name': 'name', 'label': 'Nombre', 'type': 'search', 'placeholder': 'Buscar producto...'},
            {'name': 'category', 'label': 'Categoría', 'type': 'select', 'options': [
                {'value': cat.id, 'label': cat.name} for cat in Category.objects.all()  # 👈 Sin is_active
            ]},
            {'name': 'product_type', 'label': 'Tipo', 'type': 'select', 'options': [
                {'value': 'fabrica', 'label': 'Producto de fábrica'},
                {'value': 'coleccion_limitada', 'label': 'Colección limitada'},
            ]},
            {'name': 'is_active', 'label': 'Estado', 'type': 'select', 'options': [
                {'value': 'true', 'label': 'Activo'},
                {'value': 'false', 'label': 'Inactivo'},
            ]},
        ]
        
        return context


class ProductCreateView(PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductCreateForm
    template_name = 'backoffice/product/product_form.html'
    permission_required = 'products.add_product'
    success_url = reverse_lazy('products:product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = 'products:product_list'
        context['is_create'] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Producto "{form.instance.name}" creado exitosamente.')
        return response


class ProductUpdateView(PermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductUpdateForm
    template_name = 'backoffice/product/product_form.html'
    permission_required = 'products.change_product'
    success_url = reverse_lazy('products:product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = 'products:product_list'
        context['is_update'] = True
        # Obtener colores y variantes para tabs
        context['product_colors'] = self.object.product_colors.filter(is_active=True)
        context['variants'] = self.object.variants.filter(is_active=True)
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Producto "{form.instance.name}" actualizado exitosamente.')
        return response


class ProductDeleteView(PermissionRequiredMixin, DeleteView):
    model = Product
    form_class = ProductDeleteForm
    template_name = 'backoffice/product/product_confirm_delete.html'
    permission_required = 'products.delete_product'
    success_url = reverse_lazy('products:product_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'Producto'
        context['object_display'] = self.get_object().name
        context['cancel_url'] = 'products:product_list'
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
        messages.success(request, f'Producto "{product_name}" movido a la papelera.')
        return redirect(self.success_url)


class ProductRestoreView(PermissionRequiredMixin, TemplateView):
    """Vista para restaurar producto desde la papelera"""
    model = Product
    form_class = ProductRestoreForm
    template_name = 'backoffice/product/product_restore.html'
    permission_required = 'products.change_product'
    success_url = reverse_lazy('products:product_trashcan')
    
    def get_object(self):
        return get_object_or_404(Product.all_objects, pk=self.kwargs['pk'], is_active=False)
    
    def get_form(self):
        return self.form_class(product=self.get_object(), data=self.request.POST or None)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['product'] = product
        context['form'] = self.get_form()
        context['cancel_url'] = 'products:product_trashcan'
        context['object_name'] = 'Producto'
        context['object_display'] = product.name
        return context
    
    def post(self, request, *args, **kwargs):
        product = self.get_object()
        form = self.get_form()
        
        if form.is_valid():
            product.restore(user=request.user)
            messages.success(request, f'Producto "{product.name}" restaurado exitosamente.')
            return redirect('products:product_list')
        
        return self.render_to_response(self.get_context_data(form=form))


class ProductTrashcanView(PermissionRequiredMixin, ListView):
    """Vista de papelera (productos eliminados)"""
    model = Product
    template_name = 'backoffice/product/product_trashcan.html'
    context_object_name = 'products'
    permission_required = 'products.view_product'
    paginate_by = 20
    
    def get_queryset(self):
        return Product.all_objects.filter(is_active=False).order_by('-deleted_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for product in context['products']:
            rows.append({
                'pk': product.pk,
                'values': [
                    product.name,
                    product.category.name if product.category else '—',
                    f'${product.price:,.0f}',
                    product.deleted_at.strftime('%d/%m/%Y %H:%M') if product.deleted_at else '—',
                ],
            })
        context['rows'] = rows
        context['headers'] = ['Nombre', 'Categoría', 'Precio', 'Eliminado el']
        return context
    
class ProductColorCreateView(PermissionRequiredMixin, CreateView):
    model = ProductColor
    form_class = ProductColorCreateForm
    template_name = 'backoffice/productcolor/productcolor_form.html'
    permission_required = 'products.add_productcolor'
    success_url = reverse_lazy('products:product_list')
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs['product_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.product
        return kwargs
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        context['cancel_url'] = 'products:product_edit'
        context['cancel_args'] = [self.product.pk]
        context['title'] = f'Agregar Color a {self.product.name}'
        return context
    
    def form_valid(self, form):
        form.instance.product = self.product
        return super().form_valid(form)


class ProductColorUpdateView(PermissionRequiredMixin, UpdateView):
    model = ProductColor
    form_class = ProductColorUpdateForm
    template_name = 'backoffice/productcolor/productcolor_form.html'
    permission_required = 'products.change_productcolor'
    success_url = reverse_lazy('products:product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.object.product
        context['cancel_url'] = 'products:product_edit'
        context['cancel_args'] = [self.object.product.pk]
        context['title'] = f'Editar Color - {self.object.color.name}'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Color "{self.object.color.name}" actualizado correctamente.')
        return redirect('products:product_edit', pk=self.object.product.pk)


class ProductColorDeleteView(PermissionRequiredMixin, DeleteView):
    model = ProductColor
    form_class = ProductColorDeleteForm
    template_name = 'backoffice/productcolor/productcolor_confirm_delete.html'
    permission_required = 'products.delete_productcolor'
    success_url = reverse_lazy('products:product_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product_color'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_color = self.get_object()
        context['product'] = product_color.product
        context['object_name'] = 'Color del producto'
        context['object_display'] = f'{product_color.color.name} para {product_color.product.name}'
        context['cancel_url'] = 'products:product_edit'
        context['cancel_args'] = [product_color.product.pk]
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
        messages.success(request, f'Color "{color_name}" eliminado correctamente.')
        return redirect('products:product_edit', pk=product_pk)
    
class ProductVariantCreateView(PermissionRequiredMixin, CreateView):
    model = ProductVariant
    form_class = ProductVariantCreateForm
    template_name = 'backoffice/productvariant/productvariant_form.html'
    permission_required = 'products.add_productvariant'
    success_url = reverse_lazy('products:product_list')
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs['product_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.product
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        if not self.object:
            self.object = self.model(product=self.product)
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        context['cancel_url'] = 'products:product_edit'
        context['cancel_args'] = [self.product.pk]
        context['title'] = f'Agregar Variante a {self.product.name}'
        return context
    
    def form_valid(self, form):
        form.instance.product = self.product
        response = super().form_valid(form)
        messages.success(self.request, f'Variante "{form.instance.product_color.color.name} - {form.instance.size.name}" agregada.')
        return redirect('products:product_edit', pk=self.product.pk)


class ProductVariantUpdateView(PermissionRequiredMixin, UpdateView):
    model = ProductVariant
    form_class = ProductVariantUpdateForm
    template_name = 'backoffice/productvariant/productvariant_form.html'
    permission_required = 'products.change_productvariant'
    success_url = reverse_lazy('products:product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.object.product
        context['cancel_url'] = 'products:product_edit'
        context['cancel_args'] = [self.object.product.pk]
        context['title'] = f'Editar Variante - {self.object.product_color.color.name} / {self.object.size.name}'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Variante actualizada correctamente.')
        return redirect('products:product_edit', pk=self.object.product.pk)


class ProductVariantDeleteView(PermissionRequiredMixin, DeleteView):
    model = ProductVariant
    form_class = ProductVariantDeleteForm
    template_name = 'backoffice/productvariant/productvariant_confirm_delete.html'
    permission_required = 'products.delete_productvariant'
    success_url = reverse_lazy('products:product_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['variant'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        variant = self.get_object()
        context['product'] = variant.product
        context['object_name'] = 'Variante'
        context['object_display'] = f'{variant.product_color.color.name} - {variant.size.name}'
        context['cancel_url'] = 'products:product_edit'
        context['cancel_args'] = [variant.product.pk]
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
        messages.success(request, f'Variante desactivada correctamente.')
        return redirect('products:product_edit', pk=product_pk)


class ProductVariantRestoreView(PermissionRequiredMixin, FormView):
    """Vista para restaurar variante"""
    form_class = ProductVariantRestoreForm
    template_name = 'backoffice/productvariant/productvariant_restore.html'
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
        context['product'] = self.variant.product
        context['object_name'] = 'Variante'
        context['object_display'] = f'{self.variant.product_color.color.name} - {self.variant.size.name}'
        context['cancel_url'] = 'products:product_edit'
        context['cancel_args'] = [self.variant.product.pk]
        return context
    
    def form_valid(self, form):
        self.variant.restore(user=self.request.user)
        messages.success(self.request, 'Variante restaurada correctamente.')
        return redirect('products:product_edit', pk=self.variant.product.pk)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error al restaurar la variante.')
        return self.render_to_response(self.get_context_data(form=form))
    
class ProductVariantTrashcanView(PermissionRequiredMixin, ListView):
    """Vista de papelera para variantes de un producto"""
    model = ProductVariant
    template_name = 'backoffice/productvariant/productvariant_trashcan.html'
    context_object_name = 'variants'
    permission_required = 'products.view_productvariant'
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs['product_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return ProductVariant.all_objects.filter(
            product=self.product,
            is_active=False
        ).order_by('-deleted_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context