# DEPURE.md — Plan de Ejecución v2 (170 hallazgos)

> Basado en `ERRORS.md` v2. Organizado por prioridad → archivo.
> 9 fases. Cada fase agrupa fixes del mismo archivo para minimizar conflictos.
> Ejecutar `DJANGO_SETTINGS_MODULE=config.settings_test pytest apps/ -v` tras cada fase.

---

## 📊 Resumen

| Fase | Prioridad | Fixes | Archivos tocados |
|------|-----------|-------|-----------------|
| 1 | 🔴 P0 | 9 | 8 |
| 2 | 🟠 P1 — orders | 10 | 4 |
| 3 | 🟠 P1 — products + core + delivery | 12 | 9 |
| 4 | 🟠 P1 — config + backoffice + cross | 8 | 8 |
| 5 | 🟡 P2 — orders (parte 1) | 11 | 4 |
| 6 | 🟡 P2 — orders (parte 2) + products | 11 | 3 |
| 7 | 🟡 P2 — core + delivery + users + backoffice + config + cross | 20 | 16 |
| 8 | 🟢 P3 — Todas las apps | 10 | 8 |
| 9 | 🟢 P3 — Restantes + cross + config | 11 | 11 |

---

# FASE 1 — 🔴 P0 Críticos (runtime crashes / data loss)

## Archivo: `apps/orders/admin.py`

**O-P0-02** — Línea 210: `cancel_orders` en `actions` no definido → `AttributeError`.
```
Eliminar 'cancel_orders' de la lista `actions` (no existe método).
```

---

## Archivo: `apps/orders/views.py`

**O-P0-01** — Líneas 724–730: Stock leak si `Session.create()` falla. `to_order_items()` ya redujo stock, el catch marca cancelado sin restaurar.
```python
# Reemplazar:
order.status = STATUS_CANCELLED
order.save()
messages.error(request, f'Error al crear la sesión: {str(e)}')

# Por:
order.cancel(reason=str(e), user=request.user if request.user.is_authenticated else None)
messages.error(request, f'Error al crear la sesión de pago: {str(e)}')
```

---

## Archivo: `apps/core/admin.py`

**C-P0-01** — Línea 18: `fieldsets` referencia `'order'`, el campo se renombró a `sort_order`.
```
Cambiar 'order' → 'sort_order' en el fieldset.
```

---

## Archivo: `apps/delivery/api.py`

**D-P0-01** — Líneas 304, 312: `models.Sum()` usado sin importar `models` → `NameError`.
```
Agregar al import: from django.db.models import Q, Sum
Cambiar models.Sum(...) → Sum(...)
```

---

## Archivo: `apps/delivery/views.py`

**D-P0-02** — Línea 201: `delivery/offline.html` no existe → `TemplateDoesNotExist`.
```
Crear archivo: apps/delivery/templates/delivery/offline.html
con contenido mínimo PWA offline.
```

---

## Archivo: `apps/users/migrations/0002_create_roles_and_permissions.py`

**U-P0-01** — Línea 13: `apps.get_model('users', 'Group')` → debe ser `apps.get_model('auth', 'Group')`.
```
Cambiar 'users' → 'auth' en get_model.
```

---

## Archivo: `config/Procfile`

**CF-P0-01** — Línea 1: Comandos `manage.py` sin `DJANGO_SETTINGS_MODULE` → usan dev SQLite en prod.
```
Prefijar: DJANGO_SETTINGS_MODULE=config.settings_production python manage.py migrate && ...
```

---

## Archivo: `apps/backoffice/templates/backoffice/components/crud/list_table.html`

**X-P0-01** — Línea 19: `{{ value|safe|default:"—" }}` — XSS. Datos de usuario pasan por `mark_safe()` sin escape.
```
Buscar todas las llamadas a mark_safe() que interpolan campos de modelo en products/views.py,
core/views.py, etc. Reemplazar mark_safe(f'...{user_data}...') por format_html('...{}...', user_data).
```

---

## Archivo: `apps/products/signals.py`

**P-P0-01** — Líneas 25–27: `post_clear` itera `instance.products.all()` después del clear → vacío.
```
Agregar receiver para pre_clear que capture IDs, procesar en post_clear con los IDs capturados.
```

---

# FASE 2 — 🟠 P1 — orders/

## Archivo: `apps/orders/views.py`

**O-P1-01** — Línea 506: `item['total'] = item['price'] * item['quantity']` — string × int = repetición.
```python
item['total'] = Decimal(item['price']) * item['quantity']
```

**O-P1-08** — Líneas 810–847: Webhook no valida `amount_total` contra la orden.
```python
session = stripe.checkout.Session.retrieve(session_id)
if order.total_amount * 100 != session.amount_total:
    logger.error(f"Amount mismatch: order={order.total_amount}, stripe={session.amount_total}")
    return HttpResponse(status=200)
```

**O-P1-09** — Línea 803: `construct_event` acepta solo un secret.
```python
# settings.py:
STRIPE_WEBHOOK_KEYS = env.list('STRIPE_WEBHOOK_KEYS', default=[STRIPE_WEBHOOK_KEY])
# views.py:
stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_KEYS)
```

---

## Archivo: `apps/orders/admin.py`

**O-P1-02** — Líneas 202–208: `save_related` usa `shipping_cost` stale en memoria.
```python
def save_related(self, request, form, formsets, change):
    super().save_related(request, form, formsets, change)
    order = form.instance
    order.refresh_from_db(fields=['subtotal', 'shipping_cost'])
    order.total_amount = order.subtotal + (order.shipping_cost or 0)
    order.save(update_fields=['total_amount'])
```

**O-P1-04** — Línea 27: `is_paid` editable en admin → bypasses confirm.
```
Agregar 'is_paid' a readonly_fields.
```

**O-P1-10** — Líneas 227–257: Acciones batch sin confirmación.
```
Agregar @admin.action(description='...') y confirmation_message a cada acción.
```

---

## Archivo: `apps/orders/forms.py`

**O-P1-03** — Líneas 674–700: `OrderItemUpdateForm.save()` sin transaction ni lock.
```python
with transaction.atomic():
    variant = ProductVariant.objects.select_for_update().get(pk=self.instance.variant_id)
    diff = self.cleaned_data['quantity'] - self.original_quantity
    variant.stock -= diff
    variant.save(update_fields=['stock'])
    self.instance.save()
```

---

## Archivo: `apps/orders/models.py`

**O-P1-05** — Líneas 64–68: `customer_email` con `null=True` en `CharField`.
```
Quitar null=True, mantener blank=True.
```

**O-P1-06** — Líneas 130–137: `payment_session_id` `null=True` + `unique=True`.
```
Si no se usa fuera de Stripe: quitar unique=True, mantener null=True.
```

---

## Archivo: `apps/orders/stripe_client.py`

**O-P1-07** — Líneas 3–6: `stripe.api_version` no pineado.
```python
stripe.api_version = getattr(settings, 'STRIPE_API_VERSION', '2023-10-16')
```

---

# FASE 3 — 🟠 P1 — products + core + delivery

## Archivo: `apps/products/constants.py`

**P-P1-01** — Línea 2: `STOCK_LOW_THRESHOLD = 5` muerto (sobrescrito en línea 33).
```
Eliminar línea 2.
```

---

## Archivo: `apps/products/views.py`

**P-P1-02** — Líneas 585–590: `apply_common_filters()` duplicado.
```
Eliminar self.apply_common_filters(qs) en CollectionDetailView.get_queryset() (ya lo hace la base).
```

---

## Archivo: `apps/products/forms.py`

**P-P1-04** — Líneas 597–608: Validación de imagen solo por extensión.
```python
import magic
def clean_image(self):
    image = self.cleaned_data.get('image')
    if image:
        mime = magic.from_buffer(image.read(2048), mime=True)
        if mime not in ['image/jpeg', 'image/png', 'image/webp', 'image/gif']:
            raise ValidationError('Tipo de archivo no permitido.')
        image.seek(0)
    return image
```

**P-P1-03** — `importers/color_importer.py` línea 36: Misma validación MIME que arriba.

---

## Archivo: `apps/products/signals.py`

**P-P1-05** — Líneas 6–14: `post_save` hace query extra en cada save.
```
Usar pre_save para guardar el estado anterior en self._old_status,
comparar en post_save sin re-query.
```

**P-P1-06** — Línea 31: N+1 con `.filter().exists()` en loop.
```
Precomputar: published_ids = set(Product.objects.filter(
    collections__status='publicada', id__in=[p.id for p in productos]
).values_list('id', flat=True))
```

**P-P1-07** — Línea 12: `update_products_type()` llamado por signal + management command.
```
Eliminar la llamada del management command (archive_collections.py, publish_collections.py).
Dejar que el signal lo maneje.
```

---

## Archivo: `apps/core/views.py`

**C-P1-01** — Líneas 192–212: Emails sincrónicos en `contact()`.
```python
from threading import Thread
Thread(target=lambda: admin_email.send()).start()
# user_email ya usa fail_silently=True
```

---

## Archivo: `apps/core/context_processors.py`

**C-P1-02** — Líneas 47, 61, 75: DB queries sin cache en cada request.
```python
from django.core.cache import cache
# Categorías: cache.get/set con key f'breadcrumb_cat_{slug}'
# Producto: cache.get/set con key f'breadcrumb_prod_{slug}'
```

---

## Archivo: `apps/core/forms.py`

**C-P1-03** — Líneas 361–369: `get_button_url_choices()` hace queries en cada instanciación.
```python
from functools import lru_cache
@lru_cache(maxsize=1)
def _cached_button_choices():
    ...
```

**C-P1-04** — Líneas 146–209: `StaffLoginForm.clean()` reimplementa auth.
```
Sobrescribir confirm_login_allowed() en vez de clean().
```

---

## Archivo: `apps/delivery/views.py`

**D-P1-01** — Líneas 580–585: Summary en sesión excede límite de cookie.
```
Guardar solo: {'closed_at': date, 'total_delivered': count, 'total_amount': str(amount)}.
```

**D-P1-03** — Líneas 375–456: TOCTOU en `register_incidence`.
```python
with transaction.atomic():
    order = Order.objects.select_for_update().get(id=order_id, ...)
    order.cancel(reason=reason)
```

**D-P1-05** — Líneas 189–195: `delivery_logout` acepta GET.
```
Agregar @require_POST.
```

---

## Archivo: `apps/delivery/api.py`

**D-P1-02** — Líneas 202–261: TOCTOU en incidence API.
```python
with transaction.atomic():
    order = Order.objects.select_for_update().get(id=order_id, assigned_delivery_user=user)
    if order.status in ['entregado', 'cancelado']:
        return Response(...)
    order.cancel(reason=request.data.get('reason', ''))
```

---

## Archivo: `apps/delivery/serializers.py`

**D-P1-04** — Líneas 120–124: `MarkAsPaidSerializer` importado no usado.
```
Eliminar serializer y su import en api.py.
```

---

# FASE 4 — 🟠 P1 — config + backoffice + cross

## Archivo: `config/settings_production.py`

**CF-P1-01**: Agregar `CSRF_COOKIE_HTTPONLY = True`, `CSRF_COOKIE_SAMESITE = 'Lax'`.

**CF-P1-03**: Agregar `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`.

**CF-P1-05**: Agregar `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`.

---

## Archivo: `config/settings.py`

**CF-P1-02** — Línea 16: `ALLOWED_HOSTS = ['*']` → `env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])`.

---

## Archivo: `scripts/test_*.sh` (6 archivos)

**CF-P1-04**: Cambiar `export DJANGO_SETTINGS_MODULE=config.settings` → `config.settings_test` en:
- `scripts/test_core.sh:19`
- `scripts/test_orders.sh:16`
- `scripts/test_products.sh:16`
- `scripts/test_users.sh:16`
- `scripts/test_backoffice.sh:19`
- `scripts/coverage_all.sh:20`

---

## Archivo: `apps/backoffice/metrics.py`

**B-P1-01** — Línea 135: `in_bulk(field_name='name')` con nombres no únicos.
```python
# Reemplazar in_bulk por dict comprehension tolerante a duplicados:
products_map = {}
for p in Product.objects.filter(name__in=names, is_active=True):
    if p.name not in products_map:
        products_map[p.name] = p
```

---

## Archivo: `apps/backoffice/views.py`

**B-P1-02** — Línea 824: `reports[report_type]` sin `.get()`.
```python
report_class = reports.get(report_type)
if not report_class:
    return HttpResponseBadRequest('Tipo de reporte inválido.')
```

**B-P1-03** — Líneas 430–431: "Ingreso año" muestra `week_revenue`.
```
Cambiar week_revenue → year_revenue.
```

---

## Templates XSS

**X-P1-01** — `apps/delivery/templates/delivery/base_pwa.html` líneas 74–75:
```
Agregar |escapejs: {{ user.get_full_name|default:''|escapejs }}
```

**X-P1-02** — `apps/delivery/templates/delivery/orders/list.html` línea 14:
```
{{ filter|default:"all"|escapejs }}
```

**X-P1-03** — `apps/core/templates/home.html` línea 62:
```
Remover |safe: {{ slide.title_text|linebreaksbr }}
```

**X-P1-04** — `apps/core/templates/emails/contact/user_confirmation.html` línea 39:
```
Usar {% url 'products:catalog' %} como URL absoluta.
```

**X-P1-05** — Password reset flow:
```
Agregar django.contrib.auth.views.PasswordResetView en urls.py del proyecto.
Crear templates: registration/password_reset_form.html, password_reset_email.html, etc.
```

---

# FASE 5 — 🟡 P2 — orders (parte 1: admin + models + constants)

## Archivo: `apps/orders/admin.py`

**O-P2-01** — Líneas 271–281: `app_index()` muerto en `OrderAdmin`. → Eliminar método.

**O-P2-02** — Líneas 182–200: `save_model` redundante.
```python
def save_model(self, request, obj, form, change):
    if not change:
        obj.created_by = request.user
    obj.updated_by = request.user
    super().save_model(request, obj, form, change)
```

**O-P2-15** — Línea 196: `import uuid` inline. → Eliminar (campo ya tiene `default=uuid.uuid4`).

**O-P2-16** — Línea 106: `is_paid` en `list_filter` sin índice.
```python
# En Order.Meta.indexes:
models.Index(fields=['is_paid'], name='orders_ispaid_idx'),
```

---

## Archivo: `apps/orders/models.py`

**O-P2-17** — Línea 109: `status` sin `db_index`. → Agregar `db_index=True`.

**O-P2-18** — Línea 120: `assigned_delivery_user` sin `db_index`. → Agregar `db_index=True`.

**O-P2-19** — Línea 419: `OrderItem.__str__` accede `self.order.order_number`.
```python
def __str__(self):
    return f"{self.order_id} - {self.product_name_snapshot} x{self.quantity}"
```

---

## Archivo: `apps/orders/constants.py`

**O-P2-07** — Líneas 4, 39: `MAX_QUANTITY_PER_ITEM = 99` duplicado. → Eliminar línea 39.

**O-P3-01** — Líneas 34–35: `WEBHOOK_MAX_RETRIES`, `WEBHOOK_RETRY_DELAY` muertos. → Eliminar.

---

## Archivo: `apps/orders/models.py` (P3)

**O-P3-02** — `save()` doble en transiciones de estado. → Setear `self.updated_by = user` antes del primer `save()` en:
- `confirm()` (línea 210)
- `cancel()` (línea 249)
- `mark_as_ready()` (línea 267)
- `mark_as_preparing()` (línea 279)
- `assign_delivery()` (línea 294)
- `mark_as_delivered()` (línea 309)

---

# FASE 6 — 🟡 P2 — orders (parte 2: views + forms + stripe + email)

## Archivo: `apps/orders/views.py`

**O-P2-03** — Líneas 276–279: `hasattr(cart, 'cart')` siempre False. → Eliminar bloque muerto.

**O-P2-04** — Líneas 1189, 1257: Imports inline de `MAX_QUANTITY_PER_ITEM`. → Eliminar (usar module-level).

**O-P2-06** — Línea 637–638: `create_stripe_checkout_session` acepta GET.
```
Cambiar @require_http_methods(['GET', 'POST']) → @require_POST.
El redirect desde checkout debe ser vía POST (form con auto-submit) o mantener GET solo para
el parámetro session_id de retorno de Stripe.
```

**O-P2-11** — Línea 695: Sin `idempotency_key` en `Session.create()`.
```python
stripe.checkout.Session.create(
    ...,
    idempotency_key=str(order.order_number)
)
```

**O-P2-12** — Líneas 724–730: Stripe errors genéricos.
```python
except stripe.error.CardError as e:
    messages.error(request, f'Error con la tarjeta: {e.user_message}')
except stripe.error.StripeError as e:
    messages.error(request, 'Error con el servicio de pago. Intenta de nuevo.')
    logger.exception(...)
    order.status = STATUS_CANCELLED
    order.save()
```

**O-P2-14** — Líneas 1228–1231: `get_object()` setea `self.color`. → Mover a `form_valid()`.

**O-P2-20** — Líneas 347, 429: `cart_remove`/`cart_update` `except Exception` muy amplio.
```python
except (KeyError, ValidationError) as e:
    return JsonResponse({'success': False, 'message': str(e)}, status=400)
```

**O-P2-21** — Línea 724: No cancelar orden en Stripe errors de red.
```python
except stripe.error.APIConnectionError:
    messages.error(request, 'Error de conexión. Intenta de nuevo.')
    return redirect(ORDERS_CHECKOUT)  # No cancelar
```

**O-P2-22** — Línea 1347: `Order.objects.get(pk=order_pk)` sin guard. → `get_object_or_404(Order, pk=order_pk)`.

---

## Archivo: `apps/orders/forms.py`

**O-P2-05** — Líneas 200–242: `OrderUpdateForm` sin `clean_customer_phone`.
```
Copiar clean_customer_phone de OrderCreateForm (strip non-digits, validar longitud).
```

**O-P2-08** — Líneas 466–471: `delivery_evidence` validado pero no guardado.
```
Eliminar campo del form o agregar delivery_evidence al modelo Order.
```

---

## Archivo: `apps/orders/stripe_client.py`

**O-P2-10** — Línea 5: Fallback silencioso a mock key.
```python
secret_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
if not secret_key or secret_key == 'sk_test_mock':
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured('STRIPE_SECRET_KEY no está configurada.')
```

**O-P2-13** — Línea 4: Sin validación test/live.
```python
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

if not settings.DEBUG and not settings.STRIPE_SECRET_KEY.startswith('sk_live_'):
    raise ImproperlyConfigured('En producción se requiere una key live de Stripe.')
```

---

## Archivo: `apps/orders/email.py`

**O-P2-09** — Línea 11: URL hardcodeada.
```python
from django.urls import reverse
tracking_url = f"{settings.SITE_URL}{reverse('orders:order_tracking', kwargs={'tracking_token': order.tracking_token})}"
```

**X-P2-06** — Línea 23: `send_mail` sin try/except.
```python
try:
    send_order_confirmation_email(order)
except Exception:
    logger.exception(f"Error enviando email de confirmación para {order.order_number}")
```

---

## Archivo: `apps/orders/views.py` (X-P2-05)

**X-P2-05** — Línea 835: Email en webhook puede enviarse doble.
```
Mover send_order_confirmation_email() dentro del if order.status == STATUS_PENDING:.
```

---

# FASE 7 — 🟡 P2 — products + core + delivery + users + backoffice + config + cross

## Archivo: `apps/products/views.py`

**P-P2-01** — Líneas 694–708: `build_gallery_context` sin `.select_related('color')`.
```
product.product_colors.filter(is_active=True).select_related('color').prefetch_related('images')
```

**P-P2-02** — Líneas 728–740: `build_variants_context` sin `product_color__color`.
```
.select_related('product_color__color', 'size')
```

**P-P2-03** — Líneas 1136–1141: XSS vía `mark_safe` con `color.code`.
```python
from django.utils.html import format_html
format_html('<div style="background-color: {};"></div><span>{}</span>', color.code, color.code)
```

**P-P2-04** — Líneas 401–407: `get_base_queryset()` muerto. → Eliminar método.

**P-P2-06** — Líneas 597–610: `_sanitize_css()` con regex. → Nota: bajo riesgo (solo staff). Dejar para futura iteración.

**P-P2-07** — Líneas 359–361: 3x `.count()` separados.
```
low_stock_list = list(low_stock_variants)
out_of_stock_list = list(out_of_stock_variants)
# Usar len() en vez de .count()
```

---

## Archivo: `apps/products/forms.py`

**P-P2-05** — Líneas 111–118: `LABEL_CARD_*` duplicados. → Eliminar primer bloque.

---

## Archivo: `apps/products/models.py`

**P-P2-08** — `product_type`, `is_active` sin índice.
```python
# Product.Meta.indexes:
models.Index(fields=['product_type', 'is_active']),
```

**P-P2-09** — `Collection.status` sin índice. → `db_index=True`.

---

## Archivo: `apps/products/admin.py`

**P-P2-12** — Línea 431: `list_filter` con campos sin índice.
```python
# Agregar a Collection.Meta.indexes:
models.Index(fields=['start_date']),
models.Index(fields=['end_date']),
```

**P-P2-13** — Líneas 556–577: Acciones sin `@admin.action`.
```
Agregar @admin.action(description='...') a archive_expired_collections, 
publish_scheduled_collections, archive_selected_collections.
```

---

## Archivo: `apps/core/views.py`

**C-P2-01** — Línea 312: `staff_logout` acepta GET. → `@require_POST`.

**C-P2-02** — Líneas 263–298: Staff login sin prefetch de groups.
```python
user = authenticate(...)
if user:
    user = User.objects.prefetch_related('groups').get(pk=user.pk)
```

---

## Archivo: `apps/core/crud/widgets.py`

**C-P2-04** — Línea 393: URL hardcodeada. → `reverse('admin:products_product_add')`.

**C-P2-05** — Líneas 46–50, 151–154: Cache de imágenes sin invalidación.
```python
# En ProductImage.save() y .delete():
cache.delete('product_images_all')
```

---

## Archivo: `apps/core/crud/mixins.py`

**C-P2-06** — Líneas 208–220: `get_next_order()` race condition.
```python
with transaction.atomic():
    max_order = self.model.objects.select_for_update().aggregate(Max('sort_order'))['sort_order__max']
    return (max_order or 0) + 1
```

---

## Archivo: `apps/core/context_processors.py`

**C-P2-07** — Línea 175: `except Exception` → `except Resolver404`.

**C-P2-08** — Línea 62: URL con concatenación de strings.
```python
from urllib.parse import urlencode
category_url = f"{reverse('products:catalog')}?{urlencode({'category': product.category.slug})}"
```

**C-P2-09** — Líneas 46–82: Sin catch para DB errors.
```python
try:
    # DB queries
except (OperationalError, InterfaceError):
    return {'breadcrumbs': _build_simple_breadcrumb('Inicio')}
```

---

## Archivo: `apps/core/forms.py`

**C-P2-10** — Línea 367: `.select_related('category')` innecesario.
```
Product.objects.filter(is_active=True).only('slug', 'name')[:10]
```

---

## Archivo: `apps/core/models.py`

**C-P2-11** — `HeroConfig.background_image` sin validación de tamaño.
```python
# En HeroConfigForm:
def clean_background_image(self):
    img = self.cleaned_data.get('background_image')
    if img and img.size > 5 * 1024 * 1024:
        raise ValidationError('La imagen no puede superar 5MB.')
    return img
```

**C-P2-12** — `overlay_opacity` sin `verbose_name`. → Agregar `verbose_name='Opacidad del overlay'`.

---

## Archivo: `apps/delivery/views.py`

**D-P2-01** — Líneas 287–291: `order_detail` sin `prefetch_related('items')`.
```python
order = get_object_or_404(
    Order.objects.prefetch_related('items'),
    id=order_id, assigned_delivery_user=request.user
)
```

**D-P2-02** — Líneas 25, 27, 31: Imports de constantes no usadas.
```
Eliminar: DELIVERY_MANIFEST, DELIVERY_OFFLINE, DELIVERY_SERVICE_WORKER del import.
```

**D-P2-11** — Líneas 182–184: Mensaje de error filtra info.
```
Cambiar a: 'Usuario o contraseña incorrectos.'
```

---

## Archivo: `apps/delivery/serializers.py`

**D-P2-03** — Líneas 3, 5: `User` no usado. → Eliminar.

**D-P2-04** — Líneas 12, 18: `subtotal`, `stock_snapshot` sin `read_only=True`. → Agregar.

---

## Archivo: `apps/delivery/api.py`

**D-P2-09** — Línea 41: Import inline de `Q`. → Eliminar (ya module-level).

**D-P2-10** — Línea 1: `import django` → `from django.middleware.csrf import get_token`.

**D-P2-12** — Todas las APIView: Sin rate limiting.
```python
from rest_framework.throttling import UserRateThrottle
# Agregar a cada clase:
throttle_classes = [UserRateThrottle]
```

---

## Archivo: `apps/delivery/urls.py`

**D-P2-05** — Líneas 22–25: `static.serve` en prod → Reemplazar con view dedicada que sirva sw.js.

**D-P2-06** — Agregar header `Service-Worker-Allowed` en la respuesta del SW.

---

## Archivo: `apps/delivery/templates/delivery/base_pwa.html`

**D-P2-07** — Líneas 112–204: Registro SW duplicado. → Eliminar versión inline, usar solo `sw-register.js`.

**D-P2-08** — Líneas 198–202: `CHECK_UPDATE` sin handler en SW. → Eliminar envío o agregar handler.

---

## Archivo: `apps/users/management/commands/setup_roles.py`

**U-P2-01** — Líneas 85–96: N+1 en grupos.
```python
staff_users.update(groups__name='Administrador')  # No funciona en M2M
# Alternativa: user.groups.add(admin_group) (idempotente), sin verificar membresía previa.
```

**U-P2-02** — Líneas 81–82: `.get()` sin try/except.
```python
admin_group = Group.objects.filter(name='Administrador').first()
if not admin_group:
    self.stderr.write('Grupo Administrador no encontrado.')
    return
```

**U-P2-06** — Línea 54: `Permission.objects.all()` carga todo en memoria. → Usar `.iterator()`.

---

## Archivo: `apps/users/migrations/0002_*.py`

**U-P2-03** — `atomic = False` → Cambiar a `atomic = True`.

**U-P2-04** — Sin dependencias de auth/contenttypes.
```python
dependencies = [
    ('users', '0001_initial'),
    ('auth', '0012_alter_user_first_name_max_length'),
    ('contenttypes', '0002_remove_content_type_name'),
]
```

---

## Archivo: `apps/users/admin.py`

**U-P2-05** — Líneas 39–40: `BaseGroup.objects.all()` → `super().get_queryset(request)`.

---

## Archivo: `apps/users/forms.py`

**U-P2-07** — Líneas 196, 233: `Group.objects.all()` en cada form. → Usar atributo de clase estático.

---

## Archivo: `apps/backoffice/reports/queries.py`

**B-P2-03** — Líneas 30, 58, 184, 200: Funciones duplicadas. → Eliminar duplicados (líneas 184+).

**B-P2-04** — Líneas 16, 181: `PAID_STATUSES` duplicado. → Consolidar al inicio.

---

## Archivo: `apps/backoffice/metrics.py`

**B-P2-01** — Línea 179: `product.total_stock()` sin guard.
```python
total = getattr(product, 'total_stock', lambda: 0)()
```

---

## Archivo: `apps/backoffice/views.py`

**B-P2-02** — Línea 280: `dispatch()` más permisivo que mixin. → Eliminar custom dispatch.

---

## Archivo: `config/settings.py` y `settings_production.py`

**CF-P2-01**: Remover `SECURE_BROWSER_XSS_FILTER = True` de ambos.

**CF-P2-02**: Agregar `SECURE_REFERRER_POLICY = 'same-origin'` en ambos.

**CF-P2-03**: Agregar `CACHES` con Redis en `settings_production.py`.

**CF-P2-04**: Línea 230: Cambiar `level: 'INFO'` → `level: 'WARNING'`.

**CF-P2-05**: Línea 12 de settings.py: `if (BASE_DIR / '.env').exists(): environ.Env.read_env(...)`.

---

## Templates cross-cutting

**X-P2-01** — `core/layouts/base.html:35`: `window.location.href = '/delivery/login/'`.
```
Usar data-delivery-login-url="{% url 'delivery:login' %}" y leer en JS.
```

**X-P2-02** — `orders/cart_detail.html:26`: `csrfToken: "{{ csrf_token }}"` sin escapejs. → `|escapejs`.

**X-P2-03** — `products/product_detail.html:129`: Igual. → `|escapejs`.

**X-P2-04** — `delivery/base_pwa.html:60`, `orders/list.html:11`: API URL hardcodeada.
```
Usar data-api-base="{% url 'delivery:api_orders' %}" y derivar base en JS.
```

---

# FASE 8 — 🟢 P3 (parte 1)

## Archivo: `apps/orders/admin.py`

**O-P3-03**: `.short_description` → `@admin.display(description='...')` en todos los métodos de display.

---

## Archivo: `apps/products/forms.py`

**P-P3-01** — Línea 1: `from datetime import timezone` muerto. → Eliminar.

---

## Archivo: `apps/products/views.py`

**P-P3-02** — Línea 755: `float(product.price)` → `str(product.price)`.

---

## Archivo: `apps/products/models.py`

**P-P3-03** — Líneas 526–528: `from datetime import datetime` inline. → Mover al top.

**P-P3-06** — Línea 221: Agregar `verbose_name_plural = 'Colores del producto'` en `ProductColor.Meta`.

---

## Archivo: `apps/products/signals.py`

**P-P3-04** — Líneas 29–36: `product.save()` individual → `Product.objects.bulk_update(products_to_update, ['product_type'])`.

**P-P3-05** — Líneas 13–14: `DoesNotExist: pass` → Agregar `logger.warning(...)`.

---

## Archivo: `apps/products/admin.py`

**P-P2-14** — `.short_description` → `@admin.display(description='...')`.

---

## Archivo: `apps/core/views.py`

**C-P3-01** — Líneas 9–10: `JsonResponse`, `get_object_or_404` no usados. → Eliminar imports.

**C-P3-02** — Líneas 281–282: `form_invalid` no-op. → Eliminar.

**C-P3-03** — Línea 219: `except Exception` → `except (smtplib.SMTPException, ConnectionRefusedError)`.

**C-P3-06** — Línea 129: `is_active=True` redundante con `ActiveManager`. → Eliminar del filter.

---

# FASE 9 — 🟢 P3 (parte 2) + restantes

## Archivo: `apps/core/context_processors.py`

**C-P3-04** — Línea 81: `except (Collection.DoesNotExist, ImportError)` → Solo `Collection.DoesNotExist`.

---

## Archivo: `apps/core/admin.py`

**C-P3-07** — `.short_description` → `@admin.display(description='...')`.

---

## Archivo: `apps/core/design_options.py` + `forms.py`

**C-P3-05** — Eliminar duplicados de choice tuples en `forms.py`, importar desde `design_options.py`.

---

## Archivo: `apps/delivery/api.py`

**D-P3-01** — Líneas 278–283: `except Exception` leak de detalles. → `except ValidationError`.

---

## Archivo: `apps/delivery/permissions.py`

**D-P3-03** — Línea 9: `request.user and` redundante. → Eliminar.

---

## Archivo: `apps/delivery/views.py`

**D-P3-05** — Líneas 64–101: Agregar `"prefer_related_applications": false` al manifest.

---

## Archivo: `apps/delivery/templates/delivery/login.html`

**D-P3-04** — Líneas 139–174: Resetear `isSubmitting = false` en branch de fallo de validación.

---

## Archivo: `static/js/delivery/sw.js`

**D-P3-06** — Líneas 64–68: `skipWaiting()` en `install` event (incondicional, respaldo).

---

## Archivo: `apps/delivery/serializers.py`

**D-P3-07** — Líneas 129–134: Mover `INCIDENCE_CHOICES` a `constants.py`.

**D-P3-08** — Líneas 24–28, 61–67: Eliminar campos explícitos redundantes (los que matchean el modelo).

---

## Archivo: `apps/users/views.py`

**U-P3-01** — Línea 403: `update_fields=[FILTER_IS_ACTIVE]` → `update_fields=['is_active']`.

**U-P3-02** — Línea 541: `FILTER_USERNAME` → `'username'` literal.

---

## Archivo: `apps/users/models.py`

**U-P3-03** — Línea 48: `.short_description` → `@property`.

---

## Archivo: `apps/backoffice/metrics.py`

**B-P3-01** — Línea 3: `Min`, `Max` no usados. → Eliminar imports.

**B-P3-02** — Línea 7: `Size`, `Category`, `Color`, `ProductImage` no usados. → Eliminar imports.

---

## Archivo: `config/.env.example`

**CF-P3-01** — Líneas 53–55: Quitar espacios antes de `=` en variables Stripe.

---

## Archivo: `config/settings_test.py`

**CF-P3-02** — Línea 155: `logging.disable(logging.CRITICAL)` → `logging.disable(logging.WARNING)`.

---

## Archivo: `config/settings_production.py`

**CF-P3-03** — Refactorizar: `from config.settings import *` + overrides (largo plazo, no urgente).

---

## Templates cross-cutting P3

**X-P3-03** — `apps/products/views.py` línea 1311: `mark_safe(f'<img ... alt="{alt_text}" ...>')`.
```python
format_html('<img src="{}" alt="{}" class="...">', img.image.url, alt_text)
```

**X-P3-04** — `apps/core/views.py` líneas 192–212: Agregar rate limiting con `django-ratelimit`.

**X-P3-05** — `apps/products/models.py` líneas 177–178: Default `alt_text` a product name si blank.

**X-P3-01** — URLs de social media: centralizar en settings o DB (largo plazo).

**X-P3-02** — CDN integrity hashes para Tailwind, HTMX, Alpine, Font Awesome (largo plazo).

---

# ⚡ Instrucciones de ejecución

1. **Branch:** `fix/errors-v2-cleanup`
2. **Baseline:** `DJANGO_SETTINGS_MODULE=config.settings_test pytest apps/ -v`
3. **Ejecutar fases en orden 1→9.** Dentro de cada fase, agrupar edits del mismo archivo.
4. **Tras cada fase:** correr tests completos.
5. **Subagentes:** pueden paralelizar fixes de archivos distintos dentro de una misma fase.
6. **No hacer commit** hasta completar todas las fases.

**Archivos más impactados (≥5 fixes):**
- `apps/orders/views.py` — 25 fixes
- `apps/orders/admin.py` — 10 fixes
- `apps/orders/models.py` — 9 fixes
- `apps/products/views.py` — 9 fixes
- `apps/delivery/api.py` — 8 fixes
- `apps/delivery/views.py` — 8 fixes
- `config/settings_production.py` — 8 fixes

---

# ✅ Estado de ejecución (v2.1 — verificado)

| Fase | Fixes | Estado |
|------|-------|--------|
| 1 — P0 | 9 | ✅ Completada |
| 2 — P1 orders | 10 | ✅ Completada |
| 3 — P1 products/core/delivery | 12 | ✅ Completada |
| 4 — P1 config/backoffice/cross | 15 | ✅ Completada |
| 5+6 — P2 orders | 22 | ✅ Completada |
| 7 — P2 resto + config | 30 | ✅ Completada |
| 8 — P3 parte 1 | 9 | ✅ Completada |
| 9 — P3 parte 2 + cross | 15 | ✅ Completada |
| Verificación post-ejecución | 5 regresiones corregidas | ✅ Ver `ERRORS.md` § Regresiones |

**Verificación:** 23/23 imports ✅ | 17/17 tests ✅ | Smoke tests de flujos críticos ✅
(checkout, login staff válido/inválido, logout POST, ProductListView, delivery logout, home, contacto, backoffice)

---

# ⏭️ Pendientes documentados (no urgentes — próxima iteración)

| # | Ítem | Razón del aplazamiento |
|---|------|------------------------|
| 1 | X-P1-05 — Password reset flow: agregar templates de `registration/` (URL `/accounts/` ya incluida en `config/urls.py`) | Requiere diseño de templates de email y formularios |
| 2 | C-P1-05 — django-axes para protección anti fuerza bruta en login | Requiere instalar y configurar paquete nuevo |
| 3 | CF-P2-03 — Redis cache en producción | Requiere provisionar Redis en Railway |
| 4 | X-P2-07 — Migrar 48 `<script>` inline a archivos externos + CSP | Refactor grande de frontend |
| 5 | X-P2-08 — Migrar JPEGs de fondo (2.3MB) a Cloudinary | Requiere subida manual + actualizar referencias |
| 6 | CF-P3-03 — Refactor `settings_production.py` a `from config.settings import *` | Riesgo de drift si se hace sin cuidado |
| 7 | D-P2-05/06 — Servir `sw.js` sin `static.serve` + header `Service-Worker-Allowed` | Requiere probar PWA en dispositivo real |
| 8 | D-P2-07/08 — Consolidar registro de SW duplicado + handler `CHECK_UPDATE` | Requiere probar PWA en dispositivo real |
| 9 | C-P2-05 — Invalidación de cache de widgets de imágenes | Bajo impacto (5 min de staleness en admin) |
| 10 | P-P2-06 — Reemplazar `_sanitize_css()` regex por librería dedicada | Bajo riesgo (solo staff con permiso) |
| 11 | X-P3-01 — Centralizar URLs de redes sociales en settings/DB | Cosmético |
| 12 | X-P3-02 — Integrity hashes (SRI) en CDNs | Requiere fijar versiones exactas de CDN |
| 13 | C-P3-06 — `home()` aún tiene `is_active=True` redundante en 2 filtros | Inofensivo (ActiveManager lo aplica igual) |
| 14 | Migración de `products` para índices nuevos (`product_type+is_active`, `Collection.status`, fechas) | Ejecutar `makemigrations products` antes del próximo deploy |

---

# 📚 Lecciones aprendidas (para futuros agentes)

1. **Nunca cambiar una vista a `@require_POST` sin auditar redirects y templates** que la referencian (REG-02, REG-03).
2. **`prefetch_related('a__b__c')` falla si algún eslabón no es relación Django** (CloudinaryField, properties). Usar `Prefetch` anidado (REG-01).
3. **En forms de autenticación, validar permisos en `confirm_login_allowed`, no en `clean()`** — tragar `ValidationError` de `super().clean()` produce `AnonymousUser` crashes (REG-05).
4. **`ALLOWED_HOSTS` debe incluir `testserver`** o el Django Test Client falla con 400 (REG-04).
5. **Cada fix debe probarse con un smoke test del flujo afectado**, no solo con la suite de unit tests — la suite actual no cubre vistas (solo modelos), por eso estas regresiones pasaron desapercibidas.
6. **La cobertura de tests es insuficiente**: 17 tests solo cubren modelos. Las vistas críticas (checkout, login, webhook) no tienen tests — esa es la deuda técnica más grande detectada.
