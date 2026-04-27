from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, ProductVariant, ProductColor, Collection, Category
from django.utils import timezone
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