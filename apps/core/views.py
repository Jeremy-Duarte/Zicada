import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.decorators.http import require_GET, require_http_methods, require_POST, require_safe

from .models import HeroConfig
from apps.products.models import Product, Collection, Category
from .forms import ContactForm, StaffLoginForm, HeroConfigCreateForm, HeroConfigUpdateForm, HeroConfigDeleteForm, HeroConfigRestoreForm
from apps.products.views import (
    PAGINATE_BY_DEFAULT,
    CONTEXT_CANCEL_URL,
    CONTEXT_OBJECT_NAME,
    CONTEXT_OBJECT_DISPLAY,
    CONTEXT_IS_CREATE,
    CONTEXT_IS_UPDATE,
    ORDER_BY_DELETED_AT,
    ORDER_BY_CREATED_AT,
    PRODUCT_TYPE_FABRICA,
    PRODUCT_TYPE_COLECCION_LIMITADA,
    PRODUCT_TYPES_DISPLAY,
)

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
@require_GET
def home(request):
    hero_slides = HeroConfig.objects.filter(is_active=True).order_by('sort_order')
    featured_collections = Collection.objects.filter(
        status='publicada',
        is_active=True
    ).order_by('-created_at')[:3]
    latest_products = Product.objects.filter(
        is_active=True
    ).select_related('category').prefetch_related('variants')[:8]
    categories = Category.objects.all().order_by('sort_order')[:4]

    context = {
        'hero_slides': hero_slides,
        'featured_collections': featured_collections,
        'latest_products': latest_products,
        'categories': categories,
    }
    return render(request, TEMPLATE_HOME, context)


@never_cache
@require_safe
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

@require_GET
def about(request):
    return render(request, TEMPLATE_ABOUT)

@require_GET
def contact(request):
    form = ContactForm()
    return render(request, TEMPLATE_CONTACT, {'form': form})

@require_http_methods(['GET', 'POST'])
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


@require_GET
def contact_success(request):
    return render(request, TEMPLATE_CONTACT_SUCCESS)


@require_GET
def returns_policy(request):
    return render(request, TEMPLATE_RETURNS)


@require_GET
def privacy_policy(request):
    return render(request, TEMPLATE_PRIVACY)

@require_GET
def terms(request):
    return render(request, TEMPLATE_TERMS)


@require_http_methods(['GET', 'POST'])
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

@require_POST
def staff_logout(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente')
    return redirect(URL_PRODUCTS_CATALOG)

# Template Paths
TEMPLATE_HERO_FORM = 'backoffice/hero/hero_form.html'
TEMPLATE_HERO_LIST = 'backoffice/hero/hero_list.html'
TEMPLATE_HERO_CONFIRM_DELETE = 'backoffice/hero/hero_confirm_delete.html'
TEMPLATE_HERO_RESTORE = 'backoffice/hero/hero_restore.html'
TEMPLATE_HERO_TRASHCAN = 'backoffice/hero/hero_trashcan.html'

# URL Names
URL_HERO_LIST = 'core:hero_list'
URL_HERO_TRASHCAN = 'core:hero_trashcan'

# Messages
MSG_HERO_CREATED = 'Slide "{title}" creado exitosamente.'
MSG_HERO_UPDATED = 'Slide "{title}" actualizado exitosamente.'
MSG_HERO_DELETED = 'Slide "{title}" movido a la papelera.'
MSG_HERO_RESTORED = 'Slide "{title}" restaurado exitosamente.'

# Headers
HEADERS_HERO = ['Título', 'Orden', 'Estado']

# Order By
ORDER_BY_DELETED_AT = '-deleted_at'

class HeroConfigListView(PermissionRequiredMixin, ListView):
    model = HeroConfig
    template_name = TEMPLATE_HERO_LIST
    context_object_name = 'hero_slides'
    permission_required = 'core.view_heroconfig'
    paginate_by = PAGINATE_BY_DEFAULT
    
    def get_queryset(self):
        return HeroConfig.objects.filter(is_active=True).order_by('sort_order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for slide in context['hero_slides']:
            rows.append({
                'pk': slide.pk,
                'values': [
                    slide.title_text,
                    slide.sort_order,
                    '<span class="px-2 py-1 text-xs rounded-full {}">{}</span>'.format(
                        'bg-green-100 text-green-700' if slide.is_active else 'bg-red-100 text-red-700',
                        'Activo' if slide.is_active else 'Inactivo'
                    ),
                ],
            })
        context['rows'] = rows
        context['headers'] = HEADERS_HERO
        return context


class HeroConfigCreateView(PermissionRequiredMixin, CreateView):
    model = HeroConfig
    form_class = HeroConfigCreateForm
    template_name = TEMPLATE_HERO_FORM
    permission_required = 'core.add_heroconfig'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = URL_HERO_LIST
        context[CONTEXT_IS_CREATE] = True
        context['background_image_url'] = ''
        return context
    
    def get_success_url(self):
        return reverse(URL_HERO_LIST)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_HERO_CREATED.format(title=form.instance.title_text))
        return response


class HeroConfigUpdateView(PermissionRequiredMixin, UpdateView):
    model = HeroConfig
    form_class = HeroConfigUpdateForm
    template_name = TEMPLATE_HERO_FORM
    permission_required = 'core.change_heroconfig'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = URL_HERO_LIST
        context[CONTEXT_IS_UPDATE] = True
        if self.object and self.object.background_image and self.object.background_image.url:
            context['background_image_url'] = self.object.background_image.url
        else:
            context['background_image_url'] = ''
        return context
    
    def get_success_url(self):
        return reverse_lazy(URL_HERO_LIST)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_HERO_UPDATED.format(title=form.instance.title_text))
        return response

class HeroConfigDeleteView(PermissionRequiredMixin, DeleteView):
    """Soft-delete slide del hero (mover a papelera)"""
    model = HeroConfig
    form_class = HeroConfigDeleteForm
    template_name = TEMPLATE_HERO_CONFIRM_DELETE
    permission_required = 'core.delete_heroconfig'
    success_url = reverse_lazy(URL_HERO_LIST)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['slide'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_OBJECT_NAME] = 'Slide del Hero'
        context[CONTEXT_OBJECT_DISPLAY] = self.get_object().title_text
        context[CONTEXT_CANCEL_URL] = URL_HERO_LIST
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.delete(request, *args, **kwargs)
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        slide = self.get_object()
        slide_title = slide.title_text
        slide.soft_delete(user=request.user)  # Usar soft_delete
        messages.success(request, MSG_HERO_DELETED.format(title=slide_title))
        return redirect(self.success_url)


class HeroConfigRestoreView(PermissionRequiredMixin, TemplateView):
    """Restaurar slide eliminado"""
    model = HeroConfig
    form_class = HeroConfigRestoreForm
    template_name = TEMPLATE_HERO_RESTORE
    permission_required = 'core.change_heroconfig'
    success_url = reverse_lazy(URL_HERO_LIST)
    
    def get_object(self):
        return get_object_or_404(HeroConfig.all_objects, pk=self.kwargs['pk'])  # Usar all_objects
    
    def get_form(self):
        return self.form_class(slide=self.get_object(), data=self.request.POST or None)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slide = self.get_object()
        context['slide'] = slide
        context['form'] = self.get_form()
        context[CONTEXT_CANCEL_URL] = URL_HERO_TRASHCAN
        context[CONTEXT_OBJECT_NAME] = 'Slide del Hero'
        context[CONTEXT_OBJECT_DISPLAY] = slide.title_text
        return context
    
    def post(self, request, *args, **kwargs):
        slide = self.get_object()
        form = self.get_form()
        if form.is_valid():
            slide.restore(user=request.user)  # Usar restore
            messages.success(request, MSG_HERO_RESTORED.format(title=slide.title_text))
            return redirect(URL_HERO_LIST)
        return self.render_to_response(self.get_context_data(form=form))


class HeroConfigTrashcanView(PermissionRequiredMixin, ListView):
    """Lista de slides eliminados (papelera)"""
    model = HeroConfig
    template_name = TEMPLATE_HERO_TRASHCAN
    context_object_name = 'hero_slides'
    permission_required = 'core.view_heroconfig'
    paginate_by = PAGINATE_BY_DEFAULT
    
    def get_queryset(self):
        # Usar all_objects para ver también los eliminados
        return HeroConfig.all_objects.filter(is_active=False).order_by('-deleted_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for slide in context['hero_slides']:
            rows.append({
                'pk': slide.pk,
                'values': [
                    slide.title_text,
                    slide.subtitle_text[:50] if slide.subtitle_text else '-',
                    slide.order,
                    slide.deleted_at.strftime('%d/%m/%Y %H:%M') if slide.deleted_at else '-',
                ],
            })
        context['rows'] = rows
        context['headers'] = ['Título', 'Subtítulo', 'Orden', 'Eliminado el']
        return context