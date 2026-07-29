# ERRORS.md — Zicada (v2 — Organizado por Apps)

> **187 findings** consolidados de 3 rondas de escaneo exhaustivo.
> Los fixes ya aplicados de la versión anterior están marcados como `[x]`.
> Organizado por app → severidad. Total: P0=15, P1=52, P2=77, P3=43.

---

# ✅ Correcciones de lógica de negocio aplicadas (v2.2)

> 13 correcciones de integridad en el flujo checkout → pago → webhook → confirmación,
> más 2 mejoras de UX (persistencia de checkout y CSRF en sidebar).
> Auditadas entre commits `5a248971..HEAD`.

| # | Problema | Síntoma | Corrección |
|---|----------|---------|------------|
| BL-01 | `customer_email` envía `None` pero modelo ya no acepta NULL (migración 0005 quitó `null=True`) | `ValidationError` al guardar orden si el usuario no ingresa email | `customer_email` → `''` en vez de `None` |
| BL-02 | Webhook marca `is_paid=True` ANTES de `order.confirm()` | Si `confirm()` falla por stock: pedido pagado pero no confirmado, sin stock reducido, sin email | `confirm()` se ejecuta primero; si falla devuelve 500 para que Stripe reintente |
| BL-03 | Webhook: discrepancia de monto devuelve `200 OK` | Stripe no reintenta; pago cobrado pero pedido no procesado | Devuelve `400` para forzar reintento de Stripe |
| BL-04 | TOCTOU en `Order.confirm()` y `Order.cancel()` | `select_related('variant')` carga variantes ANTES de `select_for_update`; stock puede estar stale | Variantes recargadas después del lock en un `variant_map` |
| BL-05 | `cart_data()` devuelve `str` en vez de `float` | Sidebar JS rompe `toLocaleString()` y comparaciones `=== 0`; mensajes de envío gratis no funcionan | Revertido a `float()` |
| BL-06 | `cart_add()` valida `quantity > stock` en vez de `(current_qty + quantity) > stock` | Mensaje de error genérico cuando se agregan más unidades de un producto ya en carrito | Validación con cantidad acumulada + mensaje específico |
| BL-07 | `order_confirmation()` eliminó polling de webhook | Usuario ve "pago en proceso" aunque ya pagó | Polling restaurado con `WEBHOOK_MAX_RETRIES` y `WEBHOOK_RETRY_DELAY` |
| BL-08 | `cart_remove()` / `cart_update()` atrapan solo `(KeyError, ValidationError)` | Errores inesperados devuelven 500 sin JSON controlado | Restaurado `except Exception` con logging |
| BL-09 | `payment_session_id` perdió `unique=True` | Riesgo de `MultipleObjectsReturned` en webhook si dos órdenes comparten session_id | Restaurado `unique=True` (migración 0007) |
| BL-10 | `stripe_client()` rechaza `sk_test_` si `DEBUG=False` | Staging/pre-producción con claves test no pueden crear sesiones de pago | Eliminada validación de `sk_live_`; solo verifica que la key no esté vacía |
| BL-11 | `OrderItemCreateForm.save()` reduce stock inmediatamente en pedidos pendientes | Inconsistente con nuevo diseño (stock solo al confirmar pago) | Solo reduce stock si el pedido NO está pendiente |
| BL-12 | Admin perdió acción `cancel_orders` | Operadores no pueden cancelar múltiples pedidos desde el listado | Restaurada acción con razón por defecto |
| BL-13 | `to_order_items()` vacía el carrito (`self.clear()`) al crear OrderItems | Si el usuario cancela en Stripe, el carrito aparece vacío | `self.clear()` eliminado de `to_order_items()`; carrito se vacía solo en `order_confirmation()` cuando `is_paid=True` |
| UX-01 | Datos de checkout se borraban al redirigir a Stripe | Usuario debía rellenar formulario si volvía atrás | `checkout_data` persiste 1 día en sesión con auto-prefill; se limpia solo al pagar |
| UX-02 | `CSRF_COOKIE_HTTPONLY=True` impide que JS lea cookie | Sidebar falla con 403 Forbidden en todas las operaciones AJAX | CSRF token inyectado via template `globalThis.cartConfig.csrfToken` |

# 🔄 Regresiones detectadas en verificación post-ejecución (v2.1)

> Estas fallas fueron INTRODUCIDAS por fixes del plan v2 y detectadas en la auditoría
> de verificación. Ya están corregidas. Se documentan para evitar repetir el patrón.

| # | Fix origen | Problema introducido | Resolución | Lección |
|---|-----------|----------------------|------------|---------|
| REG-01 | P-P1-03 (`prefetch_related('product_colors__featured_image__image')`) | `ValueError`: cadenas de prefetch no pueden cruzar campos no relacionales (`CloudinaryField`). Rompía `/products/admin/productos/` con 500. | Usar `Prefetch('product_colors', queryset=ProductColor.objects.select_related('featured_image'))`. | `prefetch_related` con `__` solo funciona si TODOS los eslabones son relaciones Django. CloudinaryField NO lo es. Siempre probar la vista después. |
| REG-02 | O-P2-06 (`create_stripe_checkout_session` → `@require_POST`) | El flujo de checkout hace `redirect()` (GET) a esta vista tras el POST del formulario. Todo el pago quedó roto con 405. | Revertido a `@require_http_methods(['GET', 'POST'])`. La guardia `checkout_data` en sesión ya previene efectos accidentales. | Antes de endurecer métodos HTTP, buscar TODOS los `redirect()` que apunten a la vista. El patrón redirect-after-POST usa GET legítimamente. |
| REG-03 | C-P2-01 (`staff_logout` → `@require_POST`) | El sidebar del backoffice usaba `<a href>` (GET) para cerrar sesión → botón roto con 405. | Template convertido a `<form method="POST">` con CSRF. | Al cambiar una vista a POST-only, auditar TODOS los templates que la referencian (`{% url %}`). |
| REG-04 | CF-P1-02 (`ALLOWED_HOSTS` env.list sin `testserver`) | El cliente de test de Django usa host `testserver` → `DisallowedHost` 400 en smoke tests y potencialmente en desarrollo vía IP local. | Agregados `testserver` y `[::1]` al default. | Cambios en `ALLOWED_HOSTS` deben incluir `testserver` o se rompe el Django Test Client. |
| REG-05 | C-P1-04 (`StaffLoginForm.clean()` reescrito) | El `clean()` tragaba `ValidationError` de credenciales inválidas → form válido sin usuario → `auth_login(request, None)` → Django usa `AnonymousUser` → `AttributeError: 'AnonymousUser' object has no attribute '_meta'` (500 en login). | Reescrito usando solo `confirm_login_allowed(user)` — el patrón idiomático de Django: `AuthenticationForm.clean()` autentica y luego llama a este hook. | NUNCA tragar `ValidationError` de `super().clean()` en forms de autenticación. Para validar permisos post-login, usar `confirm_login_allowed`, no `clean()`. |

---

# 📦 apps/orders/

## 🔴 P0 — Crítico

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| O-P0-01 | `views.py` | 724–730 | ~~Stock se pierde permanentemente si `stripe.checkout.Session.create()` falla — `to_order_items()` ya redujo stock, pero el catch solo marca cancelado sin restaurar.~~ ✅ `to_order_items()` se ejecuta DESPUÉS de crear la sesión; si Stripe falla nunca se reduce stock. | ✅ Corregido (BL-01) |
| O-P0-02 | `admin.py` | 210 | ~~`actions = ['confirm_orders', ..., 'cancel_orders']` — `cancel_orders` no está definido. `AttributeError` al cargar el admin.~~ ✅ Definido y restaurado. | ✅ Corregido (BL-12) |

## 🟠 P1 — Alto

| # | Archivo | Problema | Fix |
|---|---------|----------|------|
| O-P1-01 | `views.py` | ~~`item['total'] = item['price'] * item['quantity']` — string por int.~~ → ✅ `Decimal(item['price']) * item['quantity']` | ✅ Corregido |
| O-P1-02 | `admin.py` | ~~`save_related` con `shipping_cost` stale en memoria.~~ → ✅ `refresh_from_db(fields=['shipping_cost'])` | ✅ Corregido |
| O-P1-03 | `forms.py` | ~~`OrderItemUpdateForm.save()` sin atomic/select_for_update.~~ → ✅ Envuelto en `transaction.atomic()` | ✅ Corregido |
| O-P1-04 | `admin.py` | ~~`is_paid` editable en admin.~~ → ✅ Movido a `readonly_fields` | ✅ Corregido |
| O-P1-05 | `models.py` | ~~`customer_email` con `null=True`.~~ → ✅ Solo `blank=True` | ✅ Corregido |
| O-P1-06 | `models.py` | ~~`payment_session_id` con `null=True` + `unique=True`.~~ → ✅ `default=''` + `UniqueConstraint` condicional | ✅ Corregido (mig. 0008) |
| O-P1-07 | `stripe_client.py` | ~~`stripe.api_version` no pineado.~~ → ✅ `stripe.api_version = '2023-10-16'` | ✅ Corregido |
| O-P1-08 | `views.py` | ~~Webhook sin validación de monto.~~ → ✅ Compara `amount_total` | ✅ Corregido |
| O-P1-09 | `views.py` | ~~Webhook con un solo secret.~~ → ✅ `STRIPE_WEBHOOK_KEYS` (lista) | ✅ Corregido |
| O-P1-10 | `admin.py` | ~~Acciones batch sin confirmación.~~ → ✅ `@admin.action(description='...')` + confirmación default de Django | ✅ Corregido |

## 🟡 P2 — Medio

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| O-P2-01 | `admin.py` | 271–281 | `app_index()` definido en `OrderAdmin` — nunca llamado por Django (es método de `AdminSite`). | Eliminar método o mover lógica a `changelist_view()`. |
| O-P2-02 | `admin.py` | 182–200 | `save_model` duplica generación de `order_number` y asigna `tracking_token` (ya tiene `default=uuid.uuid4`). | Simplificar a solo setear `created_by` / `updated_by`. |
| O-P2-03 | `views.py` | 276–279 | `cart_add`: `hasattr(cart, 'cart')` siempre False — `Cart` usa `self.cart_data`. Código muerto. | Usar `cart.get_item(variant_id)` o eliminar bloque. |
| O-P2-04 | `views.py` | 1189, 1257 | `from apps.orders.constants import MAX_QUANTITY_PER_ITEM` inline 2 veces — ya importado a nivel módulo. | Eliminar imports inline. |
| O-P2-05 | `forms.py` | 200–242 | `OrderUpdateForm` no valida teléfono (solo dígitos) — inconsistente con `OrderCreateForm`. | Agregar `clean_customer_phone` a `OrderUpdateForm`. |
| O-P2-06 | `views.py` | 637–638 | `create_stripe_checkout_session` acepta GET — side-effect en GET (crea orden, reduce stock). | Restringir a `@require_POST`. |
| O-P2-07 | `constants.py` | 4, 39 | `MAX_QUANTITY_PER_ITEM = 99` duplicado. | Eliminar duplicado en línea 39. |
| O-P2-08 | `forms.py` | 466–471 | `delivery_evidence` en `OrderMarkAsDeliveredForm` se valida pero nunca se guarda. | Guardar en modelo o eliminar campo. |
| O-P2-09 | `email.py` | 11 | URL hardcodeada `f"{settings.SITE_URL}/orders/tracking/..."`. | Usar `reverse('orders:order_tracking', kwargs=...)`. |
| O-P2-10 | `stripe_client.py` | 5 | `getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_mock')` — fallback silencioso a mock key. | `raise ImproperlyConfigured` si falta la key. |
| O-P2-11 | `views.py` | 695 | `stripe.checkout.Session.create()` sin `idempotency_key`. | Pasar `idempotency_key=str(order.order_number)`. |
| O-P2-12 | `views.py` | 724–730 | Stripe errors (CardError, etc.) atrapados como `except Exception` genérico. | Mapear `stripe.error.StripeError` subclases con mensajes específicos. |
| O-P2-13 | `stripe_client.py` | 4 | Sin validación de test vs live mode (key prefix). | Validar `sk_live_` en prod, `sk_test_` en dev. |
| O-P2-14 | `views.py` | 1228–1231 | `get_object()` setea `self.color`, `self.old_quantity` — estado frágil entre métodos. | Usar `self.object` como storage o recalcular en `form_valid()`. |
| O-P2-15 | `admin.py` | 196 | `import uuid` inline en `save_model`. | Mover a nivel módulo (o eliminar — `tracking_token` ya tiene `default`). |
| O-P2-16 | `admin.py` | 106 | `list_filter = ('status', 'is_paid', ...)` — `BooleanField` sin índice. | Agregar `models.Index(fields=['is_paid'])` en Meta. |
| O-P2-17 | `models.py` | 109 | `Order.status` (CharField) sin `db_index` — filtrado en casi todas las queries. | `db_index=True`. |
| O-P2-18 | `models.py` | 120 | `Order.assigned_delivery_user` (FK) sin `db_index` — filtrado en todas las delivery views. | `db_index=True`. |
| O-P2-19 | `models.py` | 419 | `OrderItem.__str__` accede `self.order.order_number` — N+1 en admin listings. | Usar `self.order_id` (FK cacheada). |
| O-P2-20 | `views.py` | 347, 429 | `cart_remove` y `cart_update` atrapan `except Exception` — errores de DB se convierten en 400 genérico. | `except (KeyError, ValidationError)` solamente. |
| O-P2-21 | `views.py` | 724 | `create_stripe_checkout_session` cancela orden en cualquier `Exception` (transient Stripe errors matan la orden). | Solo cancelar en errores determinísticos; reintentar en errores de red. |
| O-P2-22 | `views.py` | 1347 | `OrderItemDeleteView` hace `Order.objects.get(pk=order_pk)` sin try/except — si la orden se borró concurrentemente, error 500. | `get_object_or_404()`. |

## 🟢 P3 — Bajo

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| O-P3-01 | `constants.py` | 34–35 | `WEBHOOK_MAX_RETRIES`, `WEBHOOK_RETRY_DELAY` — importados pero nunca usados (busy-wait eliminado). | Eliminar constantes + imports. |
| O-P3-02 | `models.py` | 214, 220, 249, 257, etc. | `save()` doble en cada método de transición de estado. | Setear `updated_by` antes del primer `save()`. |
| O-P3-03 | `admin.py` | 85, 92, 144, etc. | `.short_description` en vez de `@admin.display()` (deprecado en Django 3.2+). | Migrar a `@admin.display(description='...')`. |

---

# 📦 apps/products/

## 🔴 P0 — Crítico

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| P-P0-01 | `signals.py` | 25–27 | `post_clear`: `instance.products.all()` retorna queryset vacío (productos ya removidos). `product_type` nunca se actualiza a 'fabrica'. | Capturar IDs en `pre_clear` y procesar en `post_clear`. |

## 🟠 P1 — Alto

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| P-P1-01 | `constants.py` | 2, 33 | `STOCK_LOW_THRESHOLD = 5` sobrescrito por `= 10` en línea 33— valor 5 muerto. | Eliminar línea 2, mantener 10. |
| P-P1-02 | `views.py` | 585–590 | `CollectionDetailView.get_queryset()` aplica `apply_common_filters()` dos veces — redundante, segundo `.order_by()` pisa al primero. | Remover `apply_common_filters()` duplicado. |
| P-P1-03 | `importers/color_importer.py` | 36 | `ColorImporter.validate_field` solo valida extensión de archivo, no MIME type. | Validar MIME con `python-magic`. |
| P-P1-04 | `forms.py` | 597–608 | `ProductImageForm.clean_image()` solo valida extensión de archivo — `.jpg` con PHP pasa. | `magic.from_buffer(image.read(2048), mime=True)` validar MIME. |
| P-P1-05 | `signals.py` | 6–14 | `post_save` en Collection dispara DB query (`Collection.objects.get(pk=...)`) en cada save. | Usar `pre_save` para comparar estado anterior. |
| P-P1-06 | `signals.py` | 31 | `for product in productos: product.collections.filter(...).exists()` — N+1. | Precomputar set de product IDs con colecciones publicadas. |
| P-P1-07 | `signals.py` | 12 | `instance.update_products_type()` llamado por signal Y por el management command — doble invocación. | Remover la llamada duplicada del command o del signal. |

## 🟡 P2 — Medio

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| P-P2-01 | `views.py` | 694–708 | `build_gallery_context`: falta `.select_related('color')` — N+1 por `pc.color.id/name/code`. | Agregar `.select_related('color')`. |
| P-P2-02 | `views.py` | 728–740 | `build_variants_context`: falta `.select_related('product_color__color')` — N+1. | Agregar `.select_related('product_color__color')`. |
| P-P2-03 | `views.py` | 1136–1141 | `color.code` en `mark_safe(f'...style="background-color: {color.code};"')` — XSS si se inserta raw. | `format_html()` con escaping. |
| P-P2-04 | `views.py` | 401–407 | `BaseProductListView.get_base_queryset()` nunca llamado — código muerto. | Eliminar o refactorizar `get_queryset()` para usarlo. |
| P-P2-05 | `forms.py` | 111–118, 1495–1502 | `LABEL_CARD_*` constants definidos dos veces — el primer bloque es código muerto. | Eliminar duplicado. |
| P-P2-06 | `views.py` | 597–610 | `_sanitize_css()` usa regex blacklist — frágil contra bypasses (`@import`, `-moz-binding`). | Usar biblioteca de sanitización CSS (cssutils, bleach). |
| P-P2-07 | `views.py` | 359–361 | `StockDashboardView`: 3x `.count()` separados cuando los querysets ya están evaluados. | Evaluar a listas primero, usar `len()`. |
| P-P2-08 | `models.py` | 260, 277 | `Product.slug` tiene `unique=True` (índice implícito), pero `product_type` e `is_active` no — filtrados en queries de catálogo. | `db_index=True` en `product_type` + `is_active`. |
| P-P2-09 | `models.py` | 581 | `Collection.status` (CharField) sin `db_index` — filtrado en casi todas las queries. | `db_index=True`. |
| P-P2-10 | `models.py` | 513 | `ProductVariant.__str__` accede `self.product.name`, `self.product_color.color.name`, `self.size.name` — 3 FK traversals. | Usar `select_related()` en todas las vistas que muestran variantes. |
| P-P2-11 | `models.py` | 224 | `ProductColor.__str__` accede `self.product.name` + `self.color.name` — 2 FK traversals. | Asegurar `select_related('product', 'color')` en listados. |
| P-P2-12 | `admin.py` | 431 | `list_filter` incluye `start_date`, `end_date` sin índice. | Agregar índices o sacar del filter. |
| P-P2-13 | `admin.py` | 556–577 | Acciones batch (`archive_expired_collections`, etc.) sin confirmación. | Agregar `@admin.action(description='...')`. |
| P-P2-14 | `admin.py` | 61, 86, 137, etc. | `.short_description` en vez de `@admin.display()`. | Migrar a decorator. |

## 🟢 P3 — Bajo

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| P-P3-01 | `forms.py` | 1 | `from datetime import timezone` — import muerto, nunca usado. | Eliminar línea. |
| P-P3-02 | `views.py` | 755 | `float(product.price)` en JSON — pérdida de precisión Decimal. | `str(product.price)`. |
| P-P3-03 | `models.py` | 526–528 | `from datetime import datetime` inline en `save()`. | Mover a nivel módulo. |
| P-P3-04 | `signals.py` | 29–36 | `product.save()` individual en loop — debería ser `bulk_update()`. | `Product.objects.bulk_update(to_update, ['product_type'])`. |
| P-P3-05 | `signals.py` | 13–14 | `Collection.DoesNotExist: pass` sin logging. | Agregar `logger.warning()`. |
| P-P3-06 | `models.py` | 218–221 | `ProductColor.Meta` sin `verbose_name_plural`. | `verbose_name_plural = 'Colores del producto'`. |

---

# 📦 apps/core/

## 🔴 P0 — Crítico

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| C-P0-01 | `admin.py` | 18 | `fieldsets` referencia `'order'` — el campo fue renombrado a `sort_order` en migración 0003. Admin roto. | Cambiar `'order'` → `'sort_order'`. |

## 🟠 P1 — Alto

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| C-P1-01 | `views.py` | 192–212 | `contact()` envía 2 emails sincrónicos — bloquea el request thread. | Usar background thread o task queue. |
| C-P1-02 | `context_processors.py` | 47, 61, 75 | `breadcrumbs()` hace DB queries en cada request sin cache. | Cachear lookups de categoría/producto con TTL corto. |
| C-P1-03 | `forms.py` | 361–369 | `get_button_url_choices()` ejecuta DB queries en cada instanciación de formulario. | Cachear con `lru_cache` o evaluar perezosamente. |
| C-P1-04 | `forms.py` | 146–209 | `StaffLoginForm.clean()` reimplementa lógica de autenticación — bypasses rate-limit hooks de Django. | Override `confirm_login_allowed()` en vez de `clean()`. |
| C-P1-05 | `views.py` | 256–309, `delivery/views.py` 160–186 | Sin protección de fuerza bruta en login (sin django-axes, sin CAPTCHA). | Instalar y configurar `django-axes`. |

## 🟡 P2 — Medio

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| C-P2-01 | `views.py` | 312 | `staff_logout` acepta GET — CSRF-based logout. | `@require_POST`. |
| C-P2-02 | `views.py` | 263–298 | Staff login consulta `user.groups.filter(...)` sin `prefetch_related('groups')`. | Prefetch o anotar. |
| C-P2-03 | `context_processors.py` | 87–88 | `breadcrumbs()` se ejecuta en cada request pero contextualizado por vista. | Pasar breadcrumbs desde la vista en vez de context processor. |
| C-P2-04 | `crud/widgets.py` | 393 | URL hardcodeada `/products/admin/productos/crear/`. | `reverse('admin:products_product_add')`. |
| C-P2-05 | `crud/widgets.py` | 46–50, 151–154 | Cache de imágenes por 5 min sin invalidación al subir imagen nueva. | Invalidar cache en `ProductImage.save()` / `delete()`. |
| C-P2-06 | `crud/mixins.py` | 208–220 | `get_next_order()` — race condition: `max_order + 1` no es atómico. | Envolver en `transaction.atomic()` + `select_for_update()`. |
| C-P2-07 | `context_processors.py` | 175 | `except Exception` en breadcrumb resolver — atrapa `KeyboardInterrupt`. | `except Resolver404`. |
| C-P2-08 | `context_processors.py` | 62 | URL de breadcrumb construida con concatenación de strings en vez de `urlencode`. | `urllib.parse.urlencode({'category': product.category.slug})`. |
| C-P2-09 | `context_processors.py` | 46–82 | Sin try/except para DB errors — 500 en todas las páginas si DB cae. | Try/except amplio que retorna breadcrumb mínimo. |
| C-P2-10 | `forms.py` | 352–373 | `get_button_url_choices()` usa `select_related('category')` pero no usa datos de categoría. | Simplificar a `.only('slug', 'name')`. |
| C-P2-11 | `models.py` | 113–119 | `HeroConfig.background_image` y `Collection` images sin validación de tamaño de archivo. | Agregar `clean_*` methods con límite de tamaño. |
| C-P2-12 | `models.py` | 120–123 | `HeroConfig.overlay_opacity` sin `verbose_name`. | Agregar `verbose_name='Opacidad del overlay'`. |

## 🟢 P3 — Bajo

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| C-P3-01 | `views.py` | 9–10 | `JsonResponse`, `get_object_or_404` importados pero no usados. | Eliminar imports. |
| C-P3-02 | `views.py` | 281–282 | `StaffLoginView.form_invalid` es no-op (solo `return super()`). | Eliminar método. |
| C-P3-03 | `views.py` | 219 | `except Exception` en contact form atrapa `KeyboardInterrupt`. | `except smtplib.SMTPException, ConnectionRefusedError`. |
| C-P3-04 | `context_processors.py` | 81 | `except (Collection.DoesNotExist, ImportError)` — `ImportError` nunca ocurre aquí. | Solo `except Collection.DoesNotExist`. |
| C-P3-05 | `design_options.py` + `forms.py` | múltiple | Choice tuples duplicados entre archivos. | Consolidar en `design_options.py`, importar desde `forms.py`. |
| C-P3-06 | `views.py` | 129 | `home()` filtra `is_active=True` explícito + `ActiveManager` — redundante. | Eliminar `is_active=True` del filter (manager ya lo aplica). |
| C-P3-07 | `admin.py` | 49, 58 | `.short_description` en vez de `@admin.display()`. | Migrar. |

---

# 📦 apps/delivery/

## 🔴 P0 — Crítico

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| D-P0-01 | `api.py` | 304, 312 | `models.Sum()` usado pero `models` no está importado (se removió en limpieza). `NameError` en runtime. | `from django.db.models import Q, Sum`; usar `Sum(...)` directamente. |
| D-P0-02 | `views.py` | 201 | `delivery/offline.html` no existe — `TemplateDoesNotExist` 500. | Crear template o usar respuesta inline. |

## 🟠 P1 — Alto

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| D-P1-01 | `views.py` | 580–585 | `close_journey` guarda summary completo en sesión — puede exceder límite de cookie (4KB). | Guardar solo datos mínimos; usar DB-backed session. |
| D-P1-02 | `api.py` | 202–261 | TOCTOU: check de status y mutación sin `select_for_update()` en incidence API. | `transaction.atomic()` + `select_for_update()`. |
| D-P1-03 | `views.py` | 375–456 | TOCTOU en `register_incidence` (HTML view). | Mismo fix que D-P1-02. |
| D-P1-04 | `serializers.py` | 120–124 | `MarkAsPaidSerializer` importado pero nunca usado — API body no se valida. | Usar serializer en la vista o eliminarlo. |
| D-P1-05 | `views.py` | 189–195 | `delivery_logout` permite GET — logout vía prefetching/CSRF-free. | `@require_POST`. |

## 🟡 P2 — Medio

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| D-P2-01 | `views.py` | 287–291 | `order_detail` falta `prefetch_related('items')` — N+1 en template. | `Order.objects.prefetch_related('items')`. |
| D-P2-02 | `views.py` | 25, 27, 31 | `DELIVERY_MANIFEST`, `DELIVERY_OFFLINE`, `DELIVERY_SERVICE_WORKER` importados pero no usados. | Eliminar imports. |
| D-P2-03 | `serializers.py` | 3, 5 | `User = get_user_model()` asignado pero nunca usado. | Eliminar líneas. |
| D-P2-04 | `serializers.py` | 12, 18 | `subtotal` y `stock_snapshot` en `OrderItemSerializer` sin `read_only=True`. | Agregar `read_only=True`. |
| D-P2-05 | `urls.py` | 22–25 | `django.views.static.serve` en producción para sw.js — no recomendado. | Servir con Whitenoise o view dedicada. |
| D-P2-06 | `urls.py` | 22–25 | Sin header `Service-Worker-Allowed` — scope puede no coincidir. | Agregar header en la respuesta. |
| D-P2-07 | `base_pwa.html` | 112–204 | Registro SW duplicado: inline + `sw-register.js`. | Consolidar en uno. |
| D-P2-08 | `base_pwa.html` | 198–202 | `CHECK_UPDATE` message enviado al SW pero no hay handler registrado. | Agregar handler o eliminar envío. |
| D-P2-09 | `api.py` | 41 | `from django.db.models import Q` inline — ya importado a nivel módulo línea 11. | Eliminar import inline. |
| D-P2-10 | `api.py` | 1 | `import django` — módulo completo para una sola función. | `from django.middleware.csrf import get_token`. |
| D-P2-11 | `views.py` | 182–184 | Error message filtra info ("no tienes permisos de entregador"). | Mensaje genérico "Usuario o contraseña incorrectos." |
| D-P2-12 | `api.py` | 27–366 | Sin rate limiting en API endpoints. | `throttle_classes = [UserRateThrottle]`. |

## 🟢 P3 — Bajo

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| D-P3-01 | `api.py` | 278–283 | `except Exception` devuelve `str(e)` al cliente — leak de detalles internos. | `except ValidationError` con mensaje user-facing. |
| D-P3-02 | `tests.py` | 1–3 | Test file vacío — cero cobertura. | Escribir tests para auth, state transitions, incidence. |
| D-P3-03 | `permissions.py` | 9 | `request.user and` redundante — siempre es objeto en Django. | Simplificar: `request.user.is_authenticated and ...`. |
| D-P3-04 | `login.html` | 139–174 | `isSubmitting` no se resetea si validación falla — usuario bloqueado. | Resetear flag en branch de fallo. |
| D-P3-05 | `views.py` | 64–101 | Manifest sin `prefer_related_applications: false`. | Agregar. |
| D-P3-06 | `sw.js` | 64–68 | `skipWaiting()` depende de mensaje CONFIG — puede nunca ejecutarse. | `skipWaiting()` en `install` event incondicionalmente. |
| D-P3-07 | `serializers.py` | 129–134 | Incidence type choices duplicados entre serializer y view. | Mover a constantes compartidas. |
| D-P3-08 | `serializers.py` | 24–28, 61–67 | Campos explícitos redundantes en serializers. | Eliminar campos que matchean el modelo. |

---

# 📦 apps/users/

## 🔴 P0 — Crítico

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| U-P0-01 | `migrations/0002_create_roles_and_permissions.py` | 13 | `apps.get_model('users', 'Group')` — Group vive en `auth`, no en `users`. `LookupError`. | `apps.get_model('auth', 'Group')`. |

## 🟡 P2 — Medio

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| U-P2-01 | `management/commands/setup_roles.py` | 85–96 | `user.groups.filter(name=...).exists()` — N+1 por usuario. | `user.groups.add(admin_group)` (idempotente). |
| U-P2-02 | `management/commands/setup_roles.py` | 81–82 | `Group.objects.get(name='Administrador')` sin try/except. | try/except o `.filter().first()` con guard. |
| U-P2-03 | `migrations/0002_create_roles_and_permissions.py` | 101 | `atomic = False` — estado inconsistente si falla a medio camino. | `atomic = True` o transacciones parciales. |
| U-P2-04 | `migrations/0002_create_roles_and_permissions.py` | 23–24, 103–105 | Sin dependencias de `auth` o `contenttypes` — puede ejecutarse antes de que existan permisos. | Agregar `('auth', '...'), ('contenttypes', '...')` en dependencies. |
| U-P2-05 | `admin.py` | 39–40 | `GroupAdmin.get_queryset` retorna `BaseGroup.objects.all()` en vez del proxy `Group`. | `super().get_queryset(request)` o `Group.objects.all()`. |
| U-P2-06 | `management/commands/setup_roles.py` | 54 | `Permission.objects.all()` carga todos los permisos en memoria. | Usar `.iterator()`. |
| U-P2-07 | `forms.py` | 196, 233 | `Group.objects.all().order_by('name')` en cada instanciación de UserCreateForm/UpdateForm. | Cachear o usar atributo estático. |

## 🟢 P3 — Bajo

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| U-P3-01 | `views.py` | 403 | `update_fields=[FILTER_IS_ACTIVE]` — usa constante de filtro como nombre de campo. | Usar string literal `'is_active'`. |
| U-P3-02 | `views.py` | 541 | `FILTER_USERNAME` usado como campo de ordenamiento (semánticamente incorrecto). | Usar `ORDER_BY_USERNAME` o literal. |
| U-P3-03 | `models.py` | 48 | `.short_description` en modelo — debería usar `@property`. | Migrar a `@property` con nombre descriptivo. |

---

# 📦 apps/backoffice/

## 🟠 P1 — Alto

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| B-P1-01 | `metrics.py` | 135 | `Product.objects.filter(name__in=names).in_bulk(field_name='name')` — nombres no son únicos, puede crashear. | Usar `.in_bulk()` con PK o manejar duplicados. |
| B-P1-02 | `views.py` | 824 | `reports[report_type]` sin `.get()` — KeyError 500 si el tipo es inválido. | `reports.get(report_type)` con fallback. |
| B-P1-03 | `views.py` | 430–431 | "Ingreso año" muestra `week_revenue` en vez de `year_revenue`. | `year_revenue` en lugar de `week_revenue`. |

## 🟡 P2 — Medio

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| B-P2-01 | `metrics.py` | 179 | `product.total_stock()` sin verificar que el método existe. | try/except AttributeError o verificar. |
| B-P2-02 | `views.py` | 280 | `BaseDashboardView.dispatch()` es más permisivo que `StaffPermissionRequiredMixin`. | Eliminar custom dispatch; usar solo el mixin. |
| B-P2-03 | `reports/queries.py` | 30, 58, 184, 200 | Funciones duplicadas — segunda definición sobrescribe la primera. | Eliminar duplicados (mantener una versión canónica). |
| B-P2-04 | `reports/queries.py` | 16, 181 | `PAID_STATUSES` definido dos veces. | Consolidar en una declaración al inicio. |

## 🟢 P3 — Bajo

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| B-P3-01 | `metrics.py` | 3 | `Min`, `Max` importados de `django.db.models` pero no usados. | Eliminar imports. |
| B-P3-02 | `metrics.py` | 7 | `Size`, `Category`, `Color`, `ProductImage` importados no usados. | Eliminar imports. |

---

# 🏗 config/ & raíz

## 🔴 P0 — Crítico

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| CF-P0-01 | `Procfile` | 1 | `manage.py` commands sin `DJANGO_SETTINGS_MODULE=config.settings_production` — usan dev SQLite en prod. | Prefijar con `DJANGO_SETTINGS_MODULE=config.settings_production`. |

## 🟠 P1 — Alto

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| CF-P1-01 | `settings_production.py` | — | `CSRF_COOKIE_HTTPONLY` no seteado — default es False en Django. | `CSRF_COOKIE_HTTPONLY = True`. |
| CF-P1-02 | `settings.py` | 16 | `ALLOWED_HOSTS = ['*']` — acepta cualquier Host header. | `env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])`. |
| CF-P1-03 | `settings_production.py` | — | `SESSION_COOKIE_HTTPONLY` y `SESSION_COOKIE_SAMESITE` no explícitos. | Agregar explícitamente. |
| CF-P1-04 | `scripts/test_*.sh` (6 archivos) | — | Usan `DJANGO_SETTINGS_MODULE=config.settings` en vez de `config.settings_test`. | Cambiar a `config.settings_test`. |
| CF-P1-05 | `settings_production.py` | — | Sin `SECURE_PROXY_SSL_HEADER` — redirect loops detrás de Railway proxy. | `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`. |

## 🟡 P2 — Medio

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| CF-P2-01 | `settings.py:45`, `settings_production.py:211` | — | `SECURE_BROWSER_XSS_FILTER` deprecado — encabezado ya no soportado por navegadores. | Remover; considerar CSP. |
| CF-P2-02 | `settings.py`, `settings_production.py`, `settings_test.py` | — | Sin `SECURE_REFERRER_POLICY` explícito. | `SECURE_REFERRER_POLICY = 'same-origin'`. |
| CF-P2-03 | `settings_production.py` | — | Sin configuración de cache — `LocMemCache` por worker en gunicorn. | Configurar Redis cache. |
| CF-P2-04 | `settings_production.py` | 230 | Django logger en `INFO` — riesgo de loguear PII en producción. | `level: 'WARNING'`. |
| CF-P2-05 | `settings.py` | 12 | `.env` se lee sin verificar que existe — falla silenciosamente. | `if (BASE_DIR / '.env').exists():`. |

## 🟢 P3 — Bajo

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| CF-P3-01 | `.env.example` | 53–55 | Espacios antes de `=` en variables Stripe. | Quitar espacios. |
| CF-P3-02 | `settings_test.py` | 155 | `logging.disable(logging.CRITICAL)` — silencia todo. | `logging.disable(logging.WARNING)`. |
| CF-P3-03 | `settings_production.py` | — | ~70% duplicado de `settings.py` — riesgo de drift. | Refactorizar a `from config.settings import *`. |

---

# 📐 Cross-cutting (varias apps / templates)

## 🔴 P0 — Crítico

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| X-P0-01 | `backoffice/templates/.../list_table.html` | 19 | `{{ value\|safe\|default:"—" }}` — renderiza cualquier valor como HTML sin escape. Multiples vistas pasan user data a `mark_safe()` que alimenta este template. | Separar text_values (escape) de html_values (pre-sanitized). |

## 🟠 P1 — Alto

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| X-P1-01 | `delivery/base_pwa.html` | 74–75 | `user.get_full_name` y `user.username` en JS sin `\|escapejs` — XSS. | `\|escapejs`. |
| X-P1-02 | `delivery/orders/list.html` | 14 | `filter` (GET param) en JS sin `\|escapejs` — XSS vía URL. | `\|escapejs`. |
| X-P1-03 | `core/templates/home.html` | 62 | `{{ slide.title_text\|safe\|linebreaksbr }}` — staff puede inyectar `<script>`. | Remover `\|safe`. |
| X-P1-04 | `core/templates/emails/contact/user_confirmation.html` | 39 | URL hardcodeada `{{ site_url }}/catalogo/`. | `reverse('products:catalog')`. |
| X-P1-05 | Todo el proyecto | — | Sin password reset flow para staff/delivery. | Agregar `django.contrib.auth.views.PasswordResetView`. |

## 🟡 P2 — Medio

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| X-P2-01 | `core/layouts/base.html` | 35 | `window.location.href = '/delivery/login/'` — URL hardcodeada. | Usar `{% url 'delivery:login' %}` via data attribute. |
| X-P2-02 | `orders/cart_detail.html` | 26 | `csrfToken: "{{ csrf_token }}"` sin `\|escapejs`. | `\|escapejs` por defensa en profundidad. |
| X-P2-03 | `products/product_detail.html` | 129 | Mismo patrón CSRF sin `\|escapejs`. | `\|escapejs`. |
| X-P2-04 | `delivery/base_pwa.html` | 60, `orders/list.html` 11 | API base URL hardcodeada `/delivery/api`. | Usar `{% url %}` via data attribute. |
| X-P2-05 | `orders/views.py` | 835 | `send_order_confirmation_email()` en webhook — si Stripe retry, email se envía dos veces. | Mover dentro del `if order.status == STATUS_PENDING:` block. |
| X-P2-06 | `orders/email.py` | 23 | `send_mail` con `fail_silently=False` sin try/except — si falla, webhook retorna 500. | try/except + log, nunca 500 a Stripe. |
| X-P2-07 | 48 templates con `<script>` inline | — | Sin CSP nonce — violan CSP best practices. | Plan de migración a .js externos. |
| X-P2-08 | `static/` | — | Background JPEGs (2.3MB) + favicon.ico (364KB) commiteados. | Migrar a Cloudinary; dejar placeholder pequeño. |

## 🟢 P3 — Bajo

| # | Archivo | Línea | Problema | Fix |
|---|---------|-------|----------|-----|
| X-P3-01 | Múltiples templates | — | Social media URLs hardcodeadas repetidas. | Centralizar en `SiteConfiguration` o settings. |
| X-P3-02 | `base_pwa.html`, `base.html`, `backoffice_base.html` | — | CDN sin `integrity` hash ni `crossorigin`. | Agregar atributos SRI. |
| X-P3-03 | `alt_text` en `products/views.py` | 1311 | `mark_safe(f'<img ... alt="{alt_text}" ...>')` sin escaping. | `format_html()` para escapar alt_text. |
| X-P3-04 | `core/views.py` | 192–212 | Contact form sin rate limiting. | `django-ratelimit`. |
| X-P3-05 | `products/models.py` | 177–178 | `alt_text` vacío produce `alt=""` en imágenes de producto. | Default a product name cuando blank. |

---

# 📊 Resumen

## Estado actual (v2.2)

| App | P0 | P1 | P2 | P3 | Total |
|-----|----|----|----|----|-------|
| `orders/` | 0 | 0 | 6 | 1 | **7** |
| `products/` | 1 | 7 | 14 | 6 | **28** |
| `core/` | 1 | 5 | 12 | 7 | **25** |
| `delivery/` | 2 | 5 | 12 | 8 | **27** |
| `users/` | 1 | 0 | 7 | 3 | **11** |
| `backoffice/` | 0 | 3 | 4 | 2 | **9** |
| `config/` | 1 | 5 | 5 | 3 | **14** |
| Cross-cutting | 1 | 5 | 8 | 5 | **19** |
| **TOTAL** | **7** | **30** | **68** | **35** | **140** |

## ✅ Corregido en v2.2 (15 items de lógica de negocio)

| # | Descripción | Archivos |
|---|-------------|----------|
| BL-01 | `customer_email` nunca `None` | `views.py` |
| BL-02 | Webhook: `confirm()` antes de `is_paid` | `views.py` |
| BL-03 | Webhook: monto ≠ → 400 | `views.py` |
| BL-04 | TOCTOU en `confirm()` / `cancel()` | `models.py` |
| BL-05 | `cart_data` → `float` | `views.py` |
| BL-06 | `cart_add` acumula cantidad | `views.py` |
| BL-07 | Polling webhook restaurado | `views.py`, `constants.py` |
| BL-08 | `cart_remove`/`update` → `except Exception` | `views.py` |
| BL-09 | `payment_session_id` → `unique=True` | `models.py`, migración 0007 |
| BL-10 | `stripe_client` sin live key check | `stripe_client.py` |
| BL-11 | Forms no reducen stock en pendientes | `forms.py` |
| BL-12 | Admin: `cancel_orders` restaurada | `admin.py` |
| BL-13 | Carrito no se vacía hasta confirmar pago | `cart.py`, `views.py` |
| UX-01 | Checkout data persiste 1 día | `views.py` |
| UX-02 | CSRF sidebar via `cartConfig` | `cart_icon.html`, `cart.js` |
| O-P1-06 | `payment_session_id`: `null+unique` → `default=''` + `UniqueConstraint` condicional | `models.py`, migración 0008 |

> Pendientes: 140 hallazgos de los 170 originales (30 corregidos entre v2.1 y v2.2).
> Todos los bugs del flujo de transacción completo están corregidos.
> Todos los P1 de `apps/orders/` están corregidos. Los 10 items (O-P1-01 a O-P1-10) fueron resueltos en rondas anteriores o en esta ronda (O-P1-06: migración 0008).
