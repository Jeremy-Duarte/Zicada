from django.shortcuts import render
from apps.products.models import Product, Collection, Category
from django.http import JsonResponse
from django.views.decorators.cache import never_cache

def home(request):
    featured_collections = Collection.objects.filter(
        status='publicada',
        is_active=True
    ).order_by('-created_at')[:3]
    latest_products = Product.objects.filter(
        is_active=True
    ).select_related('category').prefetch_related('variants')[:8]
    
    categories = Category.objects.all().order_by('sort_order')[:4]
    
    context = {
        'featured_collections': featured_collections,
        'latest_products': latest_products,
        'categories': categories,
    }
    return render(request, 'home.html', context)

@never_cache
def pwa_manifest(request):
    manifest = {
        "name": "Zicada",
        "short_name": "Zicada",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#1a1a1a",
        "icons": []
    }
    return JsonResponse(manifest)

def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


def returns_policy(request):
    return render(request, 'returns_policy.html')


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


def terms(request):
    return render(request, 'terms.html')


def newsletter_subscribe(request):
    from django.contrib import messages
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            messages.success(request, '¡Gracias por suscribirte!')
        else:
            messages.error(request, 'Por favor ingresa un correo válido.')
    return HttpResponseRedirect(reverse('home'))