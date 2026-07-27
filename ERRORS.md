# ERRORS.md — Zicada

> **55 findings** filtered from ~1,200 raw issues. Every item here has business impact.
> Assumption: anonymous checkout is by design (no registration required). Fix top-down by tier. Check off `[x]` when resolved.

---

## 🔴 P0 — Broken business rules (10)

User-facing functionality fails or behaves incorrectly.

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `apps/orders/views.py` | 733–755 | `order_confirmation` is `@require_GET` but calls `cart.clear()` — GET destroys session state. Also busy-waits 10s (20 retries × 0.5s) polling Stripe status, blocking the request thread. | Move `cart.clear()` to Stripe webhook or checkout POST handler; remove busy-wait polling |
| 2 | `apps/orders/models.py` | 189–213 | `Order.confirm()` decrements `variant.stock` **without** `transaction.atomic()` or `select_for_update()`. TOCTOU race: two parallel confirmations silently over-decrement stock, causing negative inventory. | Wrap in `transaction.atomic()` + use `variant.objects.select_for_update()` |
| 3 | `apps/orders/forms.py` | 724–762 | `OrderItemCreateForm.save()` decrements stock (line 752) BEFORE calling `instance.save()` (line 755). If save fails, stock is already lost permanently. | Wrap both operations in `transaction.atomic()` |
| 4 | `apps/orders/views.py` | 178–199 | `take_order` view guarded only by `@staff_member_required` — any non-delivery admin can self-assign orders. Bypasses `order.assign_delivery()` model method (which validates status == 'listo'). Directly sets `order.status` and `order.assigned_delivery_user`. | Add `request.user.is_delivery` check; use `order.assign_delivery()` model method |
| 5 | `apps/orders/views.py` | 675–686 | `create_stripe_checkout_session` manually creates OrderItems with plain `ProductVariant.objects.get()` — no `select_for_update()`. `Cart.to_order_items()` (cart.py:290–353) has proper `transaction.atomic()` + locking but is **never called**. | Use `cart.to_order_items(order)` instead of manual OrderItem creation |
| 6 | `apps/orders/views.py` | 455–461, 608–610 | `cart_data` API + `_get_cart_summary_context` convert `Decimal` prices to `float()` for JSON serialization. IEEE 754 causes precision errors on COP amounts. Same bug in `delivery/views.py:537` and `delivery/api.py:343,346,353`. | Serialize as string (`str(subtotal)`) and let frontend parse, or use a custom JSON encoder |
| 7 | `apps/orders/views.py` | 153–173 | `delivery_dashboard` fetches `Order.objects.filter(status=STATUS_READY)` — exposes ALL ready orders to EVERY delivery staff member (customer names, phones, addresses). No `assigned_delivery_user` filter. | Filter by `assigned_delivery_user=request.user` |
| 8 | `apps/orders/models.py` | 214–240 | `Order.cancel()` restores stock without `transaction.atomic()` or `select_for_update()`. Two admins canceling concurrently = stock double-restored and artificially inflated. | Same fix as `confirm()` — wrap + lock |
| 9 | `apps/orders/views.py` | 830–848 | `stripe_webhook`: if `order.confirm()` raises `ValidationError` (stock vanished between payment and confirmation), webhook returns HTTP 500, Stripe retries, but `is_paid` is never set. Customer paid, order stuck in 'pendiente'. | Set `is_paid=True` BEFORE calling `confirm()`; wrap in try/except with compensation logic |
| 10 | `apps/orders/views.py` | 1334–1360 | `OrderItemDeleteView` restores stock THEN deletes OrderItem — no `transaction.atomic()`. Failure between stock restore and delete = inconsistent state (stock inflated, item still exists). | Wrap entire sequence in `transaction.atomic()` |

---

## 🟠 P1 — N+1 query performance (12)

User-facing views making unnecessary database round-trips.

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `apps/orders/views.py` | 675–676 | `.get()` per cart item inside a loop (create_stripe_checkout_session) | Bulk `filter(id__in=ids)` → dict lookup |
| 2 | `apps/products/views.py` | 342–348 | `StockDashboardView`: `product.total_stock()` + `.variants.count()` per product in loop | `Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True))` or `annotate(total=Sum('variants__stock'))` |
| 3 | `apps/products/views.py` | 1435–1456 | `ProductListView`: `get_featured_image()` per product in loop, traverses product_colors | `prefetch_related('product_colors__featured_image__image')` |
| 4 | `apps/products/views.py` | 1629–1637 | `ProductTrashcanView`: `product.category.name` per product — no `select_related('category')` | Add `select_related('category')` to queryset |
| 5 | `apps/products/views.py` | 2023, 2106 | `CollectionListView`: `collection.products.count()` per collection — `.count()` ignores prefetch | `annotate(product_count=Count('products'))` + use `collection.product_count` |
| 6 | `apps/products/views.py` | 2297–2303 | `CollectionTrashcanView`: same `.products.count()` issue | Same as #5 |
| 7 | `apps/users/views.py` | 475–478 | `GroupListView`: `group.user_set.count()` per group | `annotate(user_count=Count('user'))` + use `group.user_count` |
| 8 | `apps/backoffice/metrics.py` | 234–239 | `get_active_deliveries_list`: 2x `Order.objects.filter(...).count()` per delivery user (2N queries) | Single `User.objects.filter(...).annotate(assigned_count=Count('assigned_orders', filter=Q(...)), delivered_count=Count('assigned_orders', filter=Q(...)))` |
| 9 | `apps/backoffice/metrics.py` | 130–141 | `get_top_products`: `Product.objects.get(name=name)` per top product (N queries) | Bulk `filter(name__in=names)` → dict keyed by name |
| 10 | `apps/orders/views.py` | 762–766 | `order_confirmation`: `order.items.all()` in template, Order fetched without `prefetch_related('items')` | `Order.objects.prefetch_related('items').get(...)` |
| 11 | `apps/orders/views.py` | 775–790 | `order_tracking`: same `order.items.all()` without prefetch | Same as #10 |
| 12 | `apps/delivery/views.py` | 227–231 | `dashboard`: two querysets without `select_related`/`prefetch_related` — template accesses `order.items` | Add `.select_related('assigned_delivery_user').prefetch_related('items')` |

---

## 🟡 P2 — Code quality / constants (2)

Hardcoded values that affect correctness or user experience.

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `apps/products/constants.py` | 238 | `DATE_FILTER_LAST_YEAR = 'ultimo_ano'` — "ano" = "anus" in Spanish. Appears in URL query params and JS comparisons (`filter_sidebar.html:417-418`). | Rename to `'ultimo_anio'` (ASCII-safe n-with-tilde romanization) |
| 2 | `core/layouts/base.html:12` `backoffice/layouts/backoffice_base.html:9` `delivery/base_pwa.html:34` | — | Tailwind CDN (`cdn.tailwindcss.com`) in production templates. Adds 200KB+ JS parse per page load, runtime CSS generation on every request. | Build Tailwind at deploy time (CSS file) or use the standalone CLI; replace CDN script with static CSS link |

---

## 🟢 P3 — Typos & security hardening (11)

Code-level typos that break search/grep and security gaps.

### Typos

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `apps/conftest.py` | 16 | `product_whit_price` (whit→with) | Rename fixture (check all call sites) |
| 2 | `apps/conftest.py` | 27, 31 | `product_whit_stock`, `'Product whit Stock'` | Rename fixture + fix string |
| 3 | `apps/core/tests/conftest.py` | 6 | `product_whit_state` | Rename fixture |
| 4 | `apps/orders/tests/test_models.py` | 42 | `test_whitout_shipping_cost` | Rename test method |
| 5 | `apps/products/tests/test_models.py` | 9 | `test_prevents_deleting_product_whit_existing_orders` | Rename test method |
| 6 | `apps/conftest.py` | 20 | `f'Procucto {precio}'` → `f'Producto {precio}'` | Fix string |
| 7 | `apps/backoffice/reports/querys.py` | — | Filename `querys.py` is wrong English (should be `queries.py`). 4 files import this: `products.py:2`, `orders.py:2`, `financial.py:2`, `delivery.py:2` | Rename file → `queries.py`; update 4 import statements |
| 8 | `apps/orders/tests/conftest.py` | 11, 13 | `'Jhon Doe'` → `'John Doe'` (test data) | Fix both strings |

### Security hardening

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 9 | `apps/delivery/templates/delivery/base_pwa.html` | 69–71 | CSRF token embedded in JS globals cached by Service Worker. Subsequent page loads from cache serve stale token → cross-user CSRF failures. | Remove CSRF token from static JS globals; fetch it dynamically via a dedicated authenticated endpoint (`/delivery/api/csrf/`) |
| 10 | `config/settings.py:140–143` `config/settings_production.py:149–153` | — | DRF `DEFAULT_PERMISSION_CLASSES` = `AllowAny`. All current views override this, but **any new ViewSet/APIView added without explicit permissions will default to public**. Footgun. | Change default to `rest_framework.permissions.IsAuthenticated`; explicitly set `AllowAny` only on public views |
| 11 | `apps/orders/views.py` | 778 | Tracking tokens never expire (code comment: "los tokens no expiran"). Tokens are UUIDv4 but no TTL or rate limiting on the endpoint. | Add token expiration (e.g., 90 days) and rate limiting per IP |

---

## ⚪ P4 — Dead code & cleanup (20)

Unused files, imports, classes. SonarQube rules: python:S1128, python:S1481.

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `apps/core/views.py` | 154–167 | `pwa_manifest()` view — duplicate of `delivery/views.py:52`. Never mapped in `core/urls.py`. | Delete function + decorators |
| 2 | `apps/core/views.py` | 9 | Unused import: `HttpResponseRedirect` | Remove from import line |
| 3 | `apps/core/views.py` | 13 | Unused import: `never_cache` (only used by orphaned P1) | Remove |
| 4 | `apps/core/views.py` | 15 | Unused import: `require_POST` | Remove from import |
| 5 | `apps/core/views.py` | 15 | Unused import: `require_safe` (only used by orphaned P1) | Remove |
| 6 | `apps/core/views.py` | 45 | Unused import: `URL_HOME` from `.constants` | Remove from import |
| 7 | `apps/products/views.py` | 17 | Unused import: `require_POST` | Remove from import |
| 8 | `apps/products/views.py` | 17 | Unused import: `require_http_methods` | Remove from import |
| 9 | `apps/delivery/views.py` | 7 | Unused import: `from django.db import models` | Remove line |
| 10 | `apps/delivery/views.py` | 19 | Unused import: `from datetime import date` | Remove line |
| 11 | `apps/delivery/api.py` | 8 | Unused imports: `date`, `timedelta` | Remove from import |
| 12 | `apps/delivery/api.py` | 14–15 | Unused imports: `OrderSummarySerializer`, `MarkAsPaidSerializer` | Remove from import |
| 13 | `apps/core/crud/views.py` | 1–96 | **Entire file** unused. 5 classes (`BaseListView`, `BaseCreateView`, `BaseUpdateView`, `BaseDeleteView`, `BaseImportView`) never imported anywhere. | Delete file |
| 14 | `apps/core/crud/exports.py` | 1–120 | **Entire file** unused. 3 classes (`BaseExporter`, `ModelExporter`, `CSVImporter`) never imported. | Delete file |
| 15 | `apps/core/crud/importers/views.py` | 1–54 | **Entire file** unused. `BaseImportView` never imported (actual importers live in `products/views.py`). | Delete file |
| 16 | `apps/core/crud/mixins.py` | 16–23 | `AuditMixin` — never used outside the dead `crud/views.py` | Remove class |
| 17 | `apps/core/crud/mixins.py` | 26–32 | `SoftDeleteMixin` — same | Remove class |
| 18 | `apps/core/crud/mixins.py` | 35–41 | `RestoreMixin` — never imported anywhere | Remove class |
| 19 | `apps/core/crud/mixins.py` | 139–146 | `FormSetStyleMixin` — never imported anywhere | Remove class |
| 20 | `apps/users/forms.py` | ~596 | `DeliveryUserProfileForm` — defined but never imported/instantiated | Remove class |
| — | `apps/orders/forms.py` | ~370 | `OrderChangeStatusForm` — unused | Remove class |
| — | `apps/orders/forms.py` | ~566 | `OrderPaymentForm` — unused | Remove class |

---

## 📋 Fix order recommendation

```
stock races (P0 #2,#3,#8) → checkout bugs (P0 #1,#5,#9,#10) → precision/auth (P0 #6,#4,#7) → P1 → P3 security → P2 → P4 → P3 typos
```

Start with the stock race conditions (P0 #2, #3, #8) — these corrupt inventory which every other flow depends on. Then checkout bugs (P0 #1, #5, #9, #10) — cart clearing on GET, unused to_order_items, orphaned payments. Then precision/auth (P0 #6, #4, #7). Then N+1 perf. Then security hardening. Then constants. Then cleanup. Typos last.
