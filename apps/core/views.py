import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.decorators.cache import never_cache

from .models import HeroConfig
from apps.products.models import Product, Collection, Category
from .forms import ContactForm, StaffLoginForm

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Constants – avoid duplicated string literals
# -------------------------------------------------------------------------

TEMPLATE_HOME = 'home.html'
TEMPLATE_ABOUT = 'about.html'
TEMPLATE_CONTACT = 'contact.html'
TEMPLATE_RETURNS = 'returns_policy.html'
TEMPLATE_PRIVACY = 'privacy_policy.html'
TEMPLATE_TERMS = 'terms.html'
TEMPLATE_STAFF_LOGIN = 'core/staff_login.html'
TEMPLATE_CONTACT_SUCCESS = 'core/contact_success.html'

EMAIL_SUBJECT_PREFIX = '[Contacto Zicada] '
EMAIL_USER_SUBJECT = 'Hemos recibido tu mensaje - Zicada'
CONTACT_SUCCESS_MESSAGE = '¡Mensaje enviado con éxito! Te responderemos pronto.'
CONTACT_ERROR_MESSAGE = 'Error al enviar el mensaje. Por favor intenta de nuevo.'

URL_CORE_CONTACT = 'core:contact'
URL_CORE_CONTACT_SUCCESS = 'core:contact_success'
URL_HOME = 'home'
URL_PRODUCTS_CATALOG = 'products:catalog'
URL_BACKOFFICE_DASHBOARD = 'backoffice:dashboard'

# -------------------------------------------------------------------------
# Views
# -------------------------------------------------------------------------

def home(request):
    try:
        hero_config = HeroConfig.objects.get(is_active=True)
    except HeroConfig.DoesNotExist:
        hero_config = None
    
    featured_collections = Collection.objects.filter(
        status='publicada',
        is_active=True
    ).order_by('-created_at')[:3]
    
    latest_products = Product.objects.filter(
        is_active=True
    ).select_related('category').prefetch_related('variants')[:8]

    categories = Category.objects.all().order_by('sort_order')[:4]

    context = {
        'hero_config': hero_config,
        'featured_collections': featured_collections,
        'latest_products': latest_products,
        'categories': categories,
    }
    return render(request, TEMPLATE_HOME, context)


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
    return render(request, TEMPLATE_ABOUT)


def contact(request):
    form = ContactForm()
    return render(request, TEMPLATE_CONTACT, {'form': form})


def contact_submit(request):
    if request.method != 'POST':
        return redirect(URL_CORE_CONTACT)

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
            # Send admin notification
            admin_subject = f"{EMAIL_SUBJECT_PREFIX}{subject}"
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

            # Send user confirmation
            user_html = render_to_string('emails/contact/user_confirmation.html', context)
            user_text = render_to_string('emails/contact/user_confirmation.txt', context)

            user_email = EmailMultiAlternatives(
                subject=EMAIL_USER_SUBJECT,
                body=user_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            user_email.attach_alternative(user_html, "text/html")
            user_email.send(fail_silently=True)

            messages.success(request, CONTACT_SUCCESS_MESSAGE)
            return redirect(URL_CORE_CONTACT_SUCCESS)

        except Exception as e:
            logger.exception("Error al enviar correo de contacto")
            messages.error(request, CONTACT_ERROR_MESSAGE)
            return redirect(URL_CORE_CONTACT)

    else:
        # Show form errors
        for field, errors in form.errors.items():
            for error in errors:
                field_label = form.fields[field].label if field in form.fields else field
                messages.error(request, f'{field_label}: {error}')
        return redirect(URL_CORE_CONTACT)


def contact_success(request):
    return render(request, TEMPLATE_CONTACT_SUCCESS)


def returns_policy(request):
    return render(request, TEMPLATE_RETURNS)


def privacy_policy(request):
    return render(request, TEMPLATE_PRIVACY)


def terms(request):
    return render(request, TEMPLATE_TERMS)


def newsletter_subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            messages.success(request, '¡Gracias por suscribirte!')
        else:
            messages.error(request, 'Por favor ingresa un correo válido.')
    return HttpResponseRedirect(reverse(URL_HOME))


class StaffLoginView(LoginView):
    template_name = TEMPLATE_STAFF_LOGIN
    authentication_form = StaffLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy(URL_BACKOFFICE_DASHBOARD)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Bienvenido {self.request.user.username}')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Usuario o contraseña incorrectos')
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff or getattr(request.user, 'is_delivery', False):
                return redirect(URL_BACKOFFICE_DASHBOARD)
            return redirect(URL_PRODUCTS_CATALOG)
        return super().dispatch(request, *args, **kwargs)


def staff_logout(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente')
    return redirect(URL_PRODUCTS_CATALOG)