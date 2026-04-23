from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, ProductVariant


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