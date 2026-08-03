import logging
import smtplib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import (
    LoginView,
    PasswordResetView as BasePasswordResetView,
    PasswordResetDoneView as BasePasswordResetDoneView,
    PasswordResetConfirmView as BasePasswordResetConfirmView,
    PasswordResetCompleteView as BasePasswordResetCompleteView,
)
from django.core.mail import EmailMultiAlternatives
from django.db.models import Prefetch
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Gallery, HeroConfig, HomePromo
from apps.products.models import Collection, Product, ProductColor
from apps.core.crud.mixins import StaffPermissionRequiredMixin
from .forms import ContactForm, StaffLoginForm, HeroConfigCreateForm, HeroConfigUpdateForm, HeroConfigDeleteForm, HeroConfigRestoreForm
from apps.products.views import (
    PAGINATE_BY_DEFAULT,
    CONTEXT_CANCEL_URL,
    CONTEXT_OBJECT_NAME,
    CONTEXT_OBJECT_DISPLAY,
    CONTEXT_IS_CREATE,
    CONTEXT_IS_UPDATE,
)

logger = logging.getLogger(__name__)

from apps.core.url_names import (
    CORE_CONTACT,
    CORE_CONTACT_SUCCESS,
    CORE_HERO_LIST,
    CORE_HERO_TRASHCAN,
    CORE_STAFF_LOGIN,
    PRODUCTS_CATALOG,
    BACKOFFICE_DASHBOARD,
    DELIVERY_DASHBOARD,
)

from .constants import (
    # Collection Statuses
    COLLECTION_STATUS_PUBLISHED,
    COLLECTION_STATUS_DRAFT,
    COLLECTION_STATUS_ARCHIVED,
    # Template Paths
    TEMPLATE_HOME,
    TEMPLATE_ABOUT,
    TEMPLATE_CONTACT,
    TEMPLATE_RETURNS,
    TEMPLATE_PRIVACY,
    TEMPLATE_TERMS,
    TEMPLATE_STAFF_LOGIN,
    TEMPLATE_CONTACT_SUCCESS,
    TEMPLATE_HERO_FORM,
    TEMPLATE_HERO_LIST,
    TEMPLATE_HERO_CONFIRM_DELETE,
    TEMPLATE_HERO_RESTORE,
    TEMPLATE_HERO_TRASHCAN,
    # Password Reset Templates
    TEMPLATE_PASSWORD_RESET_FORM,
    TEMPLATE_PASSWORD_RESET_DONE,
    TEMPLATE_PASSWORD_RESET_CONFIRM,
    TEMPLATE_PASSWORD_RESET_COMPLETE,
    TEMPLATE_PASSWORD_RESET_EMAIL,
    # Email Configuration
    EMAIL_SUBJECT_PREFIX,
    EMAIL_USER_SUBJECT,
    # Contact Form Field Names
    CONTACT_FIELD_NAME,
    CONTACT_FIELD_EMAIL,
    CONTACT_FIELD_PHONE,
    CONTACT_FIELD_SUBJECT,
    CONTACT_FIELD_MESSAGE,
    # Contact Messages
    CONTACT_SUCCESS_MESSAGE,
    CONTACT_ERROR_MESSAGE,
    # Login/Logout Messages
    LOGIN_ERROR_MESSAGE,
    LOGOUT_SUCCESS_MESSAGE,
    LOGIN_WELCOME_MESSAGE,
    LOGIN_INACTIVE_MESSAGE,
    # Status Labels
    STATUS_ACTIVE_LABEL,
    STATUS_INACTIVE_LABEL,
    # Badge CSS Classes
    BADGE_ACTIVE_CSS,
    BADGE_INACTIVE_CSS,
    # Hero Section Messages
    MSG_HERO_CREATED,
    MSG_HERO_UPDATED,
    MSG_HERO_DELETED,
    MSG_HERO_RESTORED,
    # Hero Section Headers
    HEADERS_HERO,
    HEADERS_HERO_TRASHCAN,
    # Hero Section Context Keys
    CONTEXT_BACKGROUND_IMAGE_URL,
    CONTEXT_ROWS,
    CONTEXT_HEADERS,
    CONTEXT_HERO_SLIDES,
    # Hero Section Order By
    HERO_ORDER_BY_SORT,
    HERO_ORDER_BY_DELETED_AT,
    # Display Limits
    FEATURED_COLLECTIONS_LIMIT,
    HOME_PROMOS_LIMIT,
    # PWA Manifest Configuration
    PWA_NAME,
    PWA_SHORT_NAME,
    PWA_START_URL,
    PWA_DISPLAY,
    PWA_BACKGROUND_COLOR,
    PWA_THEME_COLOR,
    # Hero Section Object Names
    HERO_OBJECT_NAME,
)


@require_GET
def home(request):
    """
    HU-050 | Página de inicio personalizada
    HU-050-ALT-1: No hay slides activos → muestra hero por defecto
    HU-050-ALT-2: No hay colecciones → oculta sección
    """
    # HU-050 | H | Carga de slides activos ordenados por sort_order
    hero_slides = HeroConfig.objects.order_by(HERO_ORDER_BY_SORT)

    featured_collections = Collection.objects.filter(
        status=COLLECTION_STATUS_PUBLISHED
    ).prefetch_related(
        Prefetch(
            'products',
            queryset=Product.objects.filter(is_active=True)
                .select_related('category')
                .prefetch_related(
                    Prefetch(
                        'product_colors',
                        queryset=ProductColor.objects
                            .select_related('color', 'featured_image')
                            .prefetch_related('images')
                            .order_by('sort_order')
                    ),
                    'variants',
                )
        )
    ).order_by('-created_at')[:FEATURED_COLLECTIONS_LIMIT]

    # Espacios publicitarios configurables (máximo 3 activos)
    promos = HomePromo.objects.order_by(HERO_ORDER_BY_SORT)[:HOME_PROMOS_LIMIT]

    # Galería de fotos estilo TikTok
    gallery_items = Gallery.objects.order_by(HERO_ORDER_BY_SORT)

    context = {
        CONTEXT_HERO_SLIDES: hero_slides,
        'featured_collections': featured_collections,
        'promos': promos,
        'gallery_items': gallery_items,
    }
    return render(request, TEMPLATE_HOME, context)


@require_GET
def about(request):
    """About page view."""
    return render(request, TEMPLATE_ABOUT)


@require_http_methods(['GET', 'POST'])
def contact(request):
    """
    HU-051: Página de contacto con manejo de formulario.
    GET: Muestra formulario vacío.
    POST: Procesa el formulario.
    """
    # HU-051 | ESCENARIO 1 | E | Método GET muestra formulario
    if request.method == 'POST':
        form = ContactForm(request.POST)

        # HU-051 | ESCENARIO 2 | H | Formulario válido, procesar envío
        if form.is_valid():
            name = form.cleaned_data[CONTACT_FIELD_NAME]
            email = form.cleaned_data[CONTACT_FIELD_EMAIL]
            phone = form.cleaned_data[CONTACT_FIELD_PHONE]
            subject = form.cleaned_data[CONTACT_FIELD_SUBJECT]
            message = form.cleaned_data[CONTACT_FIELD_MESSAGE]

            context = {
                CONTACT_FIELD_NAME: name,
                CONTACT_FIELD_EMAIL: email,
                CONTACT_FIELD_PHONE: phone,
                CONTACT_FIELD_SUBJECT: subject,
                CONTACT_FIELD_MESSAGE: message,
                'site_url': settings.SITE_URL,
            }

            try:
                # HU-051 | ESCENARIO 2A | H | Enviar notificación al administrador
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
                from threading import Thread
                Thread(target=admin_email.send, daemon=True).start()

                # HU-051 | ESCENARIO 2B | H | Enviar confirmación al usuario
                user_html = render_to_string('emails/contact/user_confirmation.html', context)
                user_text = render_to_string('emails/contact/user_confirmation.txt', context)

                user_email = EmailMultiAlternatives(
                    subject=EMAIL_USER_SUBJECT,
                    body=user_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                )
                user_email.attach_alternative(user_html, "text/html")
                Thread(target=user_email.send, kwargs={'fail_silently': True}, daemon=True).start()

                # HU-051 | ESCENARIO 2C | H | Mensaje de éxito y redirección
                messages.success(request, CONTACT_SUCCESS_MESSAGE)
                return redirect(CORE_CONTACT_SUCCESS)

            # HU-051 | ESCENARIO 3 | E | Error al enviar emails
            except (smtplib.SMTPException, ConnectionRefusedError) as e:
                logger.exception(f"Error al enviar correo de contacto: {str(e)}")
                messages.error(request, CONTACT_ERROR_MESSAGE)
                return render(request, TEMPLATE_CONTACT, {'form': form})

        # HU-051 | ESCENARIO 4 | A | Formulario inválido, mostrar errores campo por campo
        # El template se encarga de mostrar form.errors junto a cada campo
        return render(request, TEMPLATE_CONTACT, {'form': form})

    form = ContactForm()
    return render(request, TEMPLATE_CONTACT, {'form': form})


@require_GET
def contact_success(request):
    """Contact form success page."""
    return render(request, TEMPLATE_CONTACT_SUCCESS)


@require_GET
def returns_policy(request):
    """Returns policy page."""
    return render(request, TEMPLATE_RETURNS)


@require_GET
def privacy_policy(request):
    """Privacy policy page."""
    return render(request, TEMPLATE_PRIVACY)


@require_GET
def terms(request):
    """Terms and conditions page."""
    return render(request, TEMPLATE_TERMS)


class StaffLoginView(LoginView):
    template_name = TEMPLATE_STAFF_LOGIN
    authentication_form = StaffLoginForm
    redirect_authenticated_user = True

    def _user_has_group(self, user, group_name: str) -> bool:
        if not user.is_authenticated:
            return False
        if not hasattr(user, '_prefetched_groups'):
            user._prefetched_groups = set(
                user.groups.values_list('name', flat=True)
            )
        return group_name in user._prefetched_groups

    def get_success_url(self):
        user = self.request.user
        
        if user.is_staff or self._user_has_group(user, 'Administrador'):
            return reverse_lazy(BACKOFFICE_DASHBOARD)
        
        if getattr(user, 'is_delivery', False) or self._user_has_group(user, 'Entregador'):
            return reverse_lazy(DELIVERY_DASHBOARD)
        
        return reverse_lazy(PRODUCTS_CATALOG)

    def form_valid(self, form):
        response = super().form_valid(form)
        
        username = self.request.user.get_full_name() or self.request.user.username
        messages.success(self.request, LOGIN_WELCOME_MESSAGE.format(username=username))
        
        return response

    def dispatch(self, request, *args, **kwargs):
        from django.contrib.messages import get_messages
        list(get_messages(request))
        
        if request.user.is_authenticated:
            if not request.user.is_active:
                messages.error(request, LOGIN_INACTIVE_MESSAGE)
                return redirect(CORE_STAFF_LOGIN)
            
            user = request.user
            
            if user.is_staff or self._user_has_group(user, 'Administrador'):
                return redirect(BACKOFFICE_DASHBOARD)
            
            if getattr(user, 'is_delivery', False) or self._user_has_group(user, 'Entregador'):
                return redirect(DELIVERY_DASHBOARD)
            
            return redirect(PRODUCTS_CATALOG)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.messages import get_messages
        context['messages'] = get_messages(self.request)
        return context


@require_POST
def staff_logout(request):
    """Staff logout view."""
    logout(request)
    messages.info(request, LOGOUT_SUCCESS_MESSAGE)
    return redirect(CORE_STAFF_LOGIN)


class HeroConfigListView(StaffPermissionRequiredMixin, ListView):
    """List active hero slides."""
    # HU-052 | ESCENARIO 1 | H | Lista slides activos
    model = HeroConfig
    template_name = TEMPLATE_HERO_LIST
    context_object_name = CONTEXT_HERO_SLIDES
    permission_required = 'core.view_heroconfig'  # HU-052 | ESCENARIO 2 | E | Sin permisos
    paginate_by = PAGINATE_BY_DEFAULT
    
    def get_queryset(self):
        return HeroConfig.objects.filter(is_active=True).order_by(HERO_ORDER_BY_SORT)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for slide in context[CONTEXT_HERO_SLIDES]:
            rows.append({
                'pk': slide.pk,
                'values': [
                    slide.title_text,
                    slide.sort_order,
                    '<span class="px-2 py-1 text-xs rounded-full {}">{}</span>'.format(
                        BADGE_ACTIVE_CSS if slide.is_active else BADGE_INACTIVE_CSS,
                        STATUS_ACTIVE_LABEL if slide.is_active else STATUS_INACTIVE_LABEL
                    ),
                ],
            })
        context[CONTEXT_ROWS] = rows
        context[CONTEXT_HEADERS] = HEADERS_HERO
        return context


class HeroConfigCreateView(StaffPermissionRequiredMixin, CreateView):
    """Create new hero slide."""
    # HU-053 | ESCENARIO 1 | H | Crear slide válido
    model = HeroConfig
    form_class = HeroConfigCreateForm
    template_name = TEMPLATE_HERO_FORM
    permission_required = 'core.add_heroconfig'  # HU-053 | ESCENARIO 3 | E | Sin permisos
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = CORE_HERO_LIST
        context[CONTEXT_IS_CREATE] = True
        context[CONTEXT_BACKGROUND_IMAGE_URL] = ''
        return context
    
    def get_success_url(self):
        return reverse(CORE_HERO_LIST)
    
    def form_valid(self, form):
        # HU-053 | ESCENARIO 1A | H | Guarda slide y muestra mensaje
        response = super().form_valid(form)
        messages.success(self.request, MSG_HERO_CREATED.format(title=form.instance.title_text))
        return response
    # HU-053 | ESCENARIO 2 | A | Formulario inválido (manejado por CreateView)


class HeroConfigUpdateView(StaffPermissionRequiredMixin, UpdateView):
    """Update existing hero slide."""
    # HU-054 | ESCENARIO 1 | H | Editar slide existente
    model = HeroConfig
    form_class = HeroConfigUpdateForm
    template_name = TEMPLATE_HERO_FORM
    permission_required = 'core.change_heroconfig'  # HU-054 | ESCENARIO 3 | E | Sin permisos
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = CORE_HERO_LIST
        context[CONTEXT_IS_UPDATE] = True
        if self.object and self.object.background_image and self.object.background_image.url:
            context[CONTEXT_BACKGROUND_IMAGE_URL] = self.object.background_image.url
        else:
            context[CONTEXT_BACKGROUND_IMAGE_URL] = ''
        return context
    
    def get_success_url(self):
        return reverse_lazy(CORE_HERO_LIST)
    
    def form_valid(self, form):
        # HU-054 | ESCENARIO 1A | H | Actualiza slide y muestra mensaje
        response = super().form_valid(form)
        messages.success(self.request, MSG_HERO_UPDATED.format(title=form.instance.title_text))
        return response
    # HU-054 | ESCENARIO 2 | A | Formulario inválido
    # HU-054 | ESCENARIO 4 | E | Slide no existe → HTTP 404


class HeroConfigDeleteView(StaffPermissionRequiredMixin, DeleteView):
    """Soft-delete hero slide (move to trashcan)."""
    # HU-055 | ESCENARIO 1 | H | Archivar slide
    model = HeroConfig
    form_class = HeroConfigDeleteForm
    template_name = TEMPLATE_HERO_CONFIRM_DELETE
    permission_required = 'core.delete_heroconfig'  # HU-055 | ESCENARIO 3 | E | Sin permisos
    success_url = reverse_lazy(CORE_HERO_LIST)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['slide'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_OBJECT_NAME] = HERO_OBJECT_NAME
        context[CONTEXT_OBJECT_DISPLAY] = self.get_object().title_text
        context[CONTEXT_CANCEL_URL] = CORE_HERO_LIST
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.delete(request, *args, **kwargs)
        # HU-055 | ESCENARIO 2 | A | Cancelar (confirmación inválida)
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        slide = self.get_object()
        slide_title = slide.title_text
        slide.soft_delete(user=request.user)
        messages.success(request, MSG_HERO_DELETED.format(title=slide_title))
        return redirect(self.success_url)


class HeroConfigRestoreView(StaffPermissionRequiredMixin, TemplateView):
    """Restore soft-deleted hero slide."""
    # HU-056 | ESCENARIO 1 | H | Restaurar slide archivado
    model = HeroConfig
    form_class = HeroConfigRestoreForm
    template_name = TEMPLATE_HERO_RESTORE
    permission_required = 'core.change_heroconfig'  # HU-056 | ESCENARIO 2 | E | Sin permisos
    success_url = reverse_lazy(CORE_HERO_LIST)
    
    def get_object(self):
        return get_object_or_404(HeroConfig.all_objects, pk=self.kwargs['pk'])
    
    def get_form(self):
        return self.form_class(slide=self.get_object(), data=self.request.POST or None)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slide = self.get_object()
        context[CONTEXT_HERO_SLIDES] = slide
        context['form'] = self.get_form()
        context[CONTEXT_CANCEL_URL] = CORE_HERO_TRASHCAN
        context[CONTEXT_OBJECT_NAME] = HERO_OBJECT_NAME
        context[CONTEXT_OBJECT_DISPLAY] = slide.title_text
        return context
    
    def post(self, request, *args, **kwargs):
        slide = self.get_object()
        form = self.get_form()
        if form.is_valid():
            slide.restore(user=request.user)
            messages.success(request, MSG_HERO_RESTORED.format(title=slide.title_text))
            return redirect(CORE_HERO_LIST)
        # HU-056 | ESCENARIO 3 | A | Confirmación inválida o conflicto de orden
        return self.render_to_response(self.get_context_data(form=form))


class HeroConfigTrashcanView(StaffPermissionRequiredMixin, ListView):
    """List soft-deleted hero slides (trashcan)."""
    # HU-057 | ESCENARIO 1 | H | Ver lista de slides archivados
    model = HeroConfig
    template_name = TEMPLATE_HERO_TRASHCAN
    context_object_name = CONTEXT_HERO_SLIDES
    permission_required = 'core.view_heroconfig'  # HU-057 | ESCENARIO 2 | E | Sin permisos
    paginate_by = PAGINATE_BY_DEFAULT
    
    def get_queryset(self):
        return HeroConfig.all_objects.filter(is_active=False).order_by(HERO_ORDER_BY_DELETED_AT)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for slide in context[CONTEXT_HERO_SLIDES]:
            rows.append({
                'pk': slide.pk,
                'values': [
                    slide.title_text,
                    slide.subtitle_text[:50] if slide.subtitle_text else '-',
                    slide.sort_order,
                    slide.deleted_at.strftime('%d/%m/%Y %H:%M') if slide.deleted_at else '-',
                ],
            })
        context[CONTEXT_ROWS] = rows
        context[CONTEXT_HEADERS] = HEADERS_HERO_TRASHCAN
        return context
    # HU-057 | ESCENARIO 3 | A | Papelera vacía (template muestra mensaje)


class PasswordResetView(BasePasswordResetView):
    template_name = TEMPLATE_PASSWORD_RESET_FORM
    email_template_name = TEMPLATE_PASSWORD_RESET_EMAIL
    success_url = reverse_lazy('core:password_reset_done')


class PasswordResetDoneView(BasePasswordResetDoneView):
    template_name = TEMPLATE_PASSWORD_RESET_DONE


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    template_name = TEMPLATE_PASSWORD_RESET_CONFIRM
    success_url = reverse_lazy('core:password_reset_complete')


class PasswordResetCompleteView(BasePasswordResetCompleteView):
    template_name = TEMPLATE_PASSWORD_RESET_COMPLETE