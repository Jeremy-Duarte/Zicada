from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, ProductVariant, ProductColor, Collection, Category, Size, Color
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import PermissionRequiredMixin
from apps.core.crud.mixins import PaginationMixin, FilterMixin
from .forms import SizeCreateForm, SizeDeleteForm, SizeUpdateForm, CategoryCreateForm, CategoryDeleteForm, CategoryUpdateForm, ColorCreateForm, ColorDeleteForm, ColorUpdateForm
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