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
)

logger = logging.getLogger(__name__)

from apps.core.url_names import (
    CORE_CONTACT,
    CORE_CONTACT_SUCCESS,
    CORE_HERO_LIST,
    CORE_HERO_TRASHCAN,
    PRODUCTS_CATALOG,
    BACKOFFICE_DASHBOARD,
)

from .constants import (
    URL_HOME,
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
    LATEST_PRODUCTS_LIMIT,
    FEATURED_CATEGORIES_LIMIT,
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
    """Home page view with hero slides, collections, products and categories."""
    hero_slides = HeroConfig.objects.filter(is_active=True).order_by(HERO_ORDER_BY_SORT)
    featured_collections = Collection.objects.filter(
        status=COLLECTION_STATUS_PUBLISHED,
        is_active=True
    ).order_by('-created_at')[:FEATURED_COLLECTIONS_LIMIT]
    latest_products = Product.objects.filter(
        is_active=True
    ).select_related('category').prefetch_related('variants')[:LATEST_PRODUCTS_LIMIT]
    categories = Category.objects.all().order_by(HERO_ORDER_BY_SORT)[:FEATURED_CATEGORIES_LIMIT]

    context = {
        CONTEXT_HERO_SLIDES: hero_slides,
        'featured_collections': featured_collections,
        'latest_products': latest_products,
        'categories': categories,
    }
    return render(request, TEMPLATE_HOME, context)


@never_cache
@require_safe
def pwa_manifest(request):
    """PWA manifest.json generator."""
    manifest = {
        "name": PWA_NAME,
        "short_name": PWA_SHORT_NAME,
        "start_url": PWA_START_URL,
        "display": PWA_DISPLAY,
        "background_color": PWA_BACKGROUND_COLOR,
        "theme_color": PWA_THEME_COLOR,
        "icons": []
    }
    return JsonResponse(manifest)


@require_GET
def about(request):
    """About page view."""
    return render(request, TEMPLATE_ABOUT)


@require_GET
def contact(request):
    """Contact page view with form."""
    form = ContactForm()
    return render(request, TEMPLATE_CONTACT, {'form': form})


@require_http_methods(['GET', 'POST'])
def contact_submit(request):
    """Handle contact form submission and send emails."""
    if request.method != 'POST':
        return redirect(CORE_CONTACT)

    form = ContactForm(request.POST)

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
            return redirect(CORE_CONTACT_SUCCESS)

        except Exception as e:
            logger.exception(f"Error al enviar correo de contacto: {str(e)}")
            messages.error(request, CONTACT_ERROR_MESSAGE)
            return redirect(CORE_CONTACT)

    else:
        # Show form errors
        for field, errors in form.errors.items():
            for error in errors:
                field_label = form.fields[field].label if field in form.fields else field
                messages.error(request, f'{field_label}: {error}')
        return redirect(CORE_CONTACT)


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
    """Custom staff login view."""
    template_name = TEMPLATE_STAFF_LOGIN
    authentication_form = StaffLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy(BACKOFFICE_DASHBOARD)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, LOGIN_WELCOME_MESSAGE.format(username=self.request.user.username))
        return response

    def form_invalid(self, form):
        messages.error(self.request, LOGIN_ERROR_MESSAGE)
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff or getattr(request.user, 'is_delivery', False):
                return redirect(BACKOFFICE_DASHBOARD)
            return redirect(PRODUCTS_CATALOG)
        return super().dispatch(request, *args, **kwargs)


@require_POST
def staff_logout(request):
    """Staff logout view."""
    logout(request)
    messages.info(request, LOGOUT_SUCCESS_MESSAGE)
    return redirect(PRODUCTS_CATALOG)


class HeroConfigListView(PermissionRequiredMixin, ListView):
    """List active hero slides."""
    model = HeroConfig
    template_name = TEMPLATE_HERO_LIST
    context_object_name = CONTEXT_HERO_SLIDES
    permission_required = 'core.view_heroconfig'
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


class HeroConfigCreateView(PermissionRequiredMixin, CreateView):
    """Create new hero slide."""
    model = HeroConfig
    form_class = HeroConfigCreateForm
    template_name = TEMPLATE_HERO_FORM
    permission_required = 'core.add_heroconfig'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = CORE_HERO_LIST
        context[CONTEXT_IS_CREATE] = True
        context[CONTEXT_BACKGROUND_IMAGE_URL] = ''
        return context
    
    def get_success_url(self):
        return reverse(CORE_HERO_LIST)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_HERO_CREATED.format(title=form.instance.title_text))
        return response


class HeroConfigUpdateView(PermissionRequiredMixin, UpdateView):
    """Update existing hero slide."""
    model = HeroConfig
    form_class = HeroConfigUpdateForm
    template_name = TEMPLATE_HERO_FORM
    permission_required = 'core.change_heroconfig'
    
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
        response = super().form_valid(form)
        messages.success(self.request, MSG_HERO_UPDATED.format(title=form.instance.title_text))
        return response


class HeroConfigDeleteView(PermissionRequiredMixin, DeleteView):
    """Soft-delete hero slide (move to trashcan)."""
    model = HeroConfig
    form_class = HeroConfigDeleteForm
    template_name = TEMPLATE_HERO_CONFIRM_DELETE
    permission_required = 'core.delete_heroconfig'
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
        return self.render_to_response(self.get_context_data(form=form))
    
    def delete(self, request, *args, **kwargs):
        slide = self.get_object()
        slide_title = slide.title_text
        slide.soft_delete(user=request.user)
        messages.success(request, MSG_HERO_DELETED.format(title=slide_title))
        return redirect(self.success_url)


class HeroConfigRestoreView(PermissionRequiredMixin, TemplateView):
    """Restore soft-deleted hero slide."""
    model = HeroConfig
    form_class = HeroConfigRestoreForm
    template_name = TEMPLATE_HERO_RESTORE
    permission_required = 'core.change_heroconfig'
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
        return self.render_to_response(self.get_context_data(form=form))


class HeroConfigTrashcanView(PermissionRequiredMixin, ListView):
    """List soft-deleted hero slides (trashcan)."""
    model = HeroConfig
    template_name = TEMPLATE_HERO_TRASHCAN
    context_object_name = CONTEXT_HERO_SLIDES
    permission_required = 'core.view_heroconfig'
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