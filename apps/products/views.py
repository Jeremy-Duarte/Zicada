from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, ProductVariant, Collection, Category

@staff_member_required
def stock_dashboard(request):
    low_stock_variants = ProductVariant.objects.low_stock().select_related('product', 'size', 'color')
    out_of_stock_variants = ProductVariant.objects.out_of_stock().select_related('product', 'size', 'color')
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
    """Catálogo de productos con filtros básicos"""
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('variants')
    categories = Category.objects.all().order_by('sort_order')
    
    # Filtros simples
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
    """Listado de colecciones públicas"""
    collections = Collection.objects.filter(
        status='publicada',
        is_active=True
    ).order_by('-created_at')
    
    context = {
        'collections': collections,
    }
    return render(request, 'products/collections_list.html', context)


def collection_detail(request, slug):
    collection = get_object_or_404(Collection, slug=slug, status='publicada', is_active=True)
    products = collection.products.filter(is_active=True)
    
    style_config = collection.style_config or {}
    
    context = {
        'collection': collection,
        'products': products,
        'style_config': style_config,
    }
    return render(request, 'products/collection_detail.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    variants = product.variants.filter(is_active=True).select_related('size', 'color')
    
    context = {
        'product': product,
        'variants': variants,
    }
    return render(request, 'products/product_detail.html', context)