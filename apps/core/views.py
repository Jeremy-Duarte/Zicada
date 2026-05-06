from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from apps.products.models import Product, Collection, Category
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from .forms import ContactForm

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


def contact_submit(request):
    if request.method != 'POST':
        return redirect('core:contact')
    
    form = ContactForm(request.POST)
    
    if form.is_valid():
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        phone = form.cleaned_data['phone']
        subject = form.cleaned_data['subject']
        message = form.cleaned_data['message']
        
        context = {
            'name': name,
            'email': email,
            'phone': phone,
            'subject': subject,
            'message': message,
            'site_url': settings.SITE_URL,
        }
        
        try:
            admin_subject = f"[Contacto Zicada] {subject}"
            admin_html = render_to_string('emails/contact/admin_notification.html', context)
            admin_text = render_to_string('emails/contact/admin_notification.txt', context)
            
            admin_email = EmailMultiAlternatives(
                subject=admin_subject,
                body=admin_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.DEFAULT_FROM_EMAIL],
            )
            admin_email.attach_alternative(admin_html, "text/html")
            admin_email.send()
            
            user_subject = "Hemos recibido tu mensaje - Zicada"
            user_html = render_to_string('emails/contact/user_confirmation.html', context)
            user_text = render_to_string('emails/contact/user_confirmation.txt', context)
            
            user_email = EmailMultiAlternatives(
                subject=user_subject,
                body=user_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            user_email.attach_alternative(user_html, "text/html")
            user_email.send(fail_silently=True)
            
            messages.success(request, '¡Mensaje enviado con éxito! Te responderemos pronto.')
            return redirect('core:contact_success')
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar correo de contacto: {e}")
            
            messages.error(request, 'Error al enviar el mensaje. Por favor intenta de nuevo.')
            return redirect('core:contact')
    
    else:
        for field, errors in form.errors.items():
            for error in errors:
                field_label = form.fields[field].label if field in form.fields else field
                messages.error(request, f'{field_label}: {error}')
        
        return redirect('core:contact')


def contact_success(request):
    """Página de éxito después de enviar el formulario"""
    return render(request, 'core/contact_success.html')

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