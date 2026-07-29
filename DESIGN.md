# Design System Zicada — Plan de Refactorización

> Estado del proyecto al momento del análisis: **Julio 2026**
> Proyecto Django 5.x con **6 apps**, **101 templates de backoffice**, **16 de PWA Delivery**, **21 de app clientes**, **4 layouts base**, **5 CSS custom**, **19 JS files**.

---

## Índice

1. [Fundamentos y Tailwind v4](#1-fundamentos-y-tailwind-v4)
2. [Parte A: App Clientes — Pendiente](#2-parte-a-app-clientes--pendiente)
3. [Parte B: App Backoffice](#3-parte-b-app-backoffice)
4. [Parte C: PWA Delivery](#4-parte-c-pwa-delivery)
5. [Estáticos y JavaScript — Refactor global](#5-estáticos-y-javascript--refactor-global)
6. [Roadmap de Ejecución](#6-roadmap-de-ejecución)

---

## 1. Fundamentos y Tailwind v4

### 1.1 Diagnóstico del estado actual

El proyecto usa **Tailwind CSS v3 via Play CDN** (`https://cdn.tailwindcss.com`) con **3 configuraciones inline** distintas:

| Layout | Config | Problema |
|--------|--------|----------|
| `layouts/base.html` | `tailwind.config = { colors: {zicada-dark, zicada-primary, zicada-accent, zicada-light} }` | Config en JS (v3), duplicada |
| `backoffice_base.html` | Idéntica a base.html | Duplicación exacta |
| `base_pwa.html` | `tailwind.config = { colors: {primary: #000000, secondary: #1a1a1a} }` | **Esquema diferente**; sin brand-accent |

Además existen **5 archivos CSS custom** que violan la regla de "no custom CSS" de `AGENTS.md`:
- `static/css/custom.css` — **vacío** (solicitud HTTP innecesaria)
- `static/css/products/product_detail.css` — 157 líneas, duplica utilidades
- `static/css/orders/checkout.css` — 86 líneas, casi idéntico a cart_detail.css
- `static/css/orders/cart_detail.css` — 76 líneas, casi idéntico a checkout.css
- `static/css/delivery/main.css` — 32 líneas (pequeño, parcialmente aceptable)

### 1.2 Migración a Tailwind v4 CDN

**Decisión:** Mantener CDN por preferencia del equipo, pero migrar a **v4 con configuración CSS-first** (`@theme`).

#### Configuración base única

Crear `/apps/core/templates/components/theme.html`:
```html
{% load static %}
<style>
  @theme {
    --color-brand-dark: #1a1a1a;
    --color-brand-primary: #2d2d2d;
    --color-brand-accent: #a91600;
    --color-brand-light: #f5f5f5;
    --color-brand-surface: #ffffff;
    --font-sans: 'Inter', system-ui, sans-serif;
    --spacing-container: 1280px;
    --radius-card: 0.75rem;
    --radius-button: 0.5rem;
    --radius-modal: 1rem;
    --shadow-card: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-elevated: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    --transition-base: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }
</style>
```

**Incluir en los 3 layouts base:**
```django
{% include 'components/theme.html' %}
```

**Remover** de todos los layouts:
- El `<script>` inline de `tailwind.config`
- La dependencia de `custom.css`

#### Cambios semánticos v3 → v4 (actualizar en todos los templates)
| v3 | v4 |
|----|-----|
| `bg-opacity-*` | `bg-black/50` (notación compacta) |
| `text-opacity-*` | `text-black/50` |
| `outline-none` | `outline-hidden` |
| `flex-shrink-0` | `shrink-0` |
| `flex-grow` | `grow` |
| `overflow-ellipsis` | `text-ellipsis` |
| `hover:bg-opacity-90` | `hover:bg-brand-accent/90` |

### 1.3 Tokens de diseño globales

| Token | CSS | Uso |
|-------|-----|-----|
| Fondo página | `bg-gray-100` (backoffice), `bg-white` (customer), `bg-gray-50` (PWA) | Cada layout decide su fondo |
| Superficie (cards) | `bg-white` | Todas las apps |
| Texto primario | `text-gray-900` | Títulos |
| Texto secundario | `text-gray-500` | Subtítulos, metadatos |
| Acción primaria | `bg-brand-accent text-white` | CTAs, botones principales |
| Acción secundaria | `border border-gray-300 text-gray-700 hover:bg-gray-50` | Botones alternativos |
| Peligro | `text-red-600` (texto) / `bg-red-600 text-white` (relleno) | Eliminaciones, cancelaciones |
| Éxito | `text-green-600` / `bg-green-600 text-white` | Confirmaciones, entregado |
| Advertencia | `text-yellow-600` / `bg-yellow-500 text-white` | Estados pendientes |

---

## 2. Parte A: App Clientes — Pendiente

### 2.1 Alcance

Esta sección queda **pendiente de ejecución** hasta que el cliente defina la nueva identidad visual para el frontend público. Se documenta aquí la deuda técnica detectada para que la reforma futura sea informada.

### 2.2 Templates afectados (21 archivos)

| App | Templates |
|-----|-----------|
| `products` | `catalog.html`, `collection_detail.html`, `collections_list.html`, `product_detail.html`, `stock_dashboard.html` |
| `products/components` | `_product_list.html`, `page_header.html`, `empty_state.html`, `pagination.html`, `filters/filter_sidebar.html` |
| `orders` | `cart_detail.html`, `cart_partial.html`, `checkout.html`, `order_confirmation.html`, `tracking.html`, `delivery_dashboard.html` |
| `core/components` | `header.html`, `footer.html`, `product_card.html`, `cart_icon.html`, `breadcrumbs.html`, `messages.html`, `form_snippet.html`, `seo_tags.html` |

### 2.3 Deuda técnica detectada

| # | Problema | Severidad | Resolver en reforma |
|---|----------|-----------|---------------------|
| 1 | `static/css/products/product_detail.css` — 157 líneas de CSS custom duplicando utilidades | **Alta** | Migrar a utilidades, eliminar archivo |
| 2 | `static/css/orders/checkout.css` + `cart_detail.css` — 90% idénticos | **Alta** | Unificar en un solo componente `order/cart_item` |
| 3 | `collection_detail.html` inyecta `<style>` con CSS variables + `safe_custom_css` | **Alta** | Reemplazar por `style="--col-primary:..."` en el contenedor + utilidades |
| 4 | `collections_list.html`: `mousemove` sin throttle + `MutationObserver` + `setInterval` persistente | **Alta** | Refactorizar JS: `requestAnimationFrame`, cleanup en `beforeunload` |
| 5 | `filter_sidebar.html`: Alpine.js + HTMX con hidratación inline; riesgo de doble envío | **Media** | Estandarizar en un solo approach |
| 6 | `product_card.html` usa `style=""` dinámico por tarjeta (inline styles) | **Media** | Usar `class` condicional o data-attributes |
| 7 | Botones primarios con padding inconsistente (`py-2.5`, `py-3`, `py-3.5`) | **Media** | Estandarizar en componente `btn_primary` |
| 8 | Grid gaps dispares (`gap-x-5 gap-y-8` vs `gap-8` vs `gap-x-8 gap-y-10`) | **Baja** | Unificar en `gap-8` |
| 9 | `empty_state.html` no soporta tema oscuro (falla en collection_detail fondo oscuro) | **Baja** | Añadir parámetro `theme="dark"` |
| 10 | `cartConfig` definido 2 veces (`cart_detail.html` + `cart_icon.html`) | **Baja** | Mover a `base.html` una vez |
| 11 | `checkout.css` renderiza raw form fields sin utilidades Tailwind | **Alta** | Aplicar `form_input` con utilidades |
| 12 | No `loading="lazy"` en thumbnails de galería de producto | **Media** | Añadir lazy loading |

### 2.4 Componentes existentes que NO requieren refactor

Los siguientes componentes ya están extraídos y solo necesitan ajustes menores:
- `components/page_header.html` — ya es componente
- `components/pagination.html` — ya es componente
- `components/empty_state.html` — ya es componente
- `components/messages.html` — ya es componente, unificar con `form_snippet.html`
- `components/product_card.html` — ya es componente (refactor inline styles)

---

## 3. Parte B: App Backoffice

### 3.1 Layout base — `backoffice_base.html`

**Problemas actuales:**
- Carga 10 scripts en el layout base (algunos externos sin `defer`)
- Inline `<style>` con `.sidebar-item`, `.scrollbar-thin`
- Colores duplicados del `tailwind.config`

**Acciones:**
1. Incluir `components/theme.html` para tokens globales
2. Mover `apexcharts` y `sortablejs` a `{% block extra_js %}` de las páginas que los necesitan
3. Añadir `defer` a todos los scripts propios
4. Mover las reglas `.sidebar-item` y `.scrollbar-thin` a un bloque `<style>` en el mismo componente del sidebar o a utilidades inline
5. Evaluar si el sidebar necesita `overflow-y-auto` para scroll vertical

**Estructura del layout post-refactor:**
```django
<body class="bg-gray-100 font-sans antialiased">
  <div class="flex h-screen overflow-hidden">
    {% include 'backoffice/components/sidebar.html' %}
    <main class="flex-1 overflow-y-auto bg-gray-100 p-6">
      {% include 'components/messages.html' %}
      <div class="max-w-7xl mx-auto space-y-6">
        {% block content %}{% endblock %}
      </div>
    </main>
  </div>
  {% block extra_js %}{% endblock %}
</body>
```

### 3.2 Componentes atómicos

Crear en `apps/backoffice/templates/backoffice/components/atoms/`.

#### `btn_primary.html`
```django
{% comment %} Props: text, href|type|submit, size(sm|md|lg), extra_classes, disabled {% endcomment %}
{% if href %}
<a href="{{ href }}"
   class="inline-flex items-center justify-center
     {% if size == 'sm' %}px-3 py-1.5 text-xs{% elif size == 'lg' %}px-6 py-3 text-base{% else %}px-5 py-2 text-sm{% endif %}
     bg-brand-accent text-white font-medium rounded-xl
     hover:bg-brand-accent/90 focus:outline-hidden focus:ring-2 focus:ring-brand-accent/50 focus:ring-offset-2
     transition-all duration-150 {{ extra_classes }}
     {% if disabled %}aria-disabled="true" tabindex="-1"{% endif %}">
  {{ text }}
</a>
{% else %}
<button type="{{ type|default:'button' }}"
   class="inline-flex items-center justify-center
     {% if size == 'sm' %}px-3 py-1.5 text-xs{% elif size == 'lg' %}px-6 py-3 text-base{% else %}px-5 py-2 text-sm{% endif %}
     bg-brand-accent text-white font-medium rounded-xl
     hover:bg-brand-accent/90 focus:outline-hidden focus:ring-2 focus:ring-brand-accent/50 focus:ring-offset-2
     transition-all duration-150 {{ extra_classes }}"
   {% if disabled %}disabled{% endif %}>
  {{ text }}
</button>
{% endif %}
```

#### `btn_secondary.html`
```django
{% comment %} Props: text, href, type, size, extra_classes {% endcomment %}
{# Misma estructura que btn_primary pero con clases: #}
{# border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 #}
{# focus:ring-gray-400 en lugar de brand-accent #}
```

#### `btn_danger.html`
```django
{# bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 #}
{# Para confirmaciones de eliminación #}
```

#### `btn_danger_text.html`
```django
{# text-red-600 hover:text-red-800 font-medium transition — para links de acción en tablas #}
```

#### `card.html`
```django
{% comment %} Props: extra_classes, padding(none|sm|md|lg) {% endcomment %}
<div class="bg-white rounded-xl shadow-sm
  {% if padding == 'none' %}{% elif padding == 'sm' %}p-4{% elif padding == 'lg' %}p-8{% else %}p-6{% endif %}
  {{ extra_classes }}">
  {{ children }}
</div>
```

#### `page_title.html`
```django
{% comment %} Props: title, subtitle {% endcomment %}
<div class="mb-6">
  <h1 class="text-2xl font-bold text-gray-900">{{ title }}</h1>
  {% if subtitle %}<p class="mt-1 text-sm text-gray-500">{{ subtitle }}</p>{% endif %}
</div>
```

#### `form_label.html`
```django
<label for="{{ for }}" class="block text-sm font-medium text-gray-700 mb-1.5">
  {{ text }}{% if required %}<span class="text-red-500 ml-0.5">*</span>{% endif %}
</label>
```

#### `form_input.html`
```django
{% comment %} Props: field (Django form field), extra_classes, placeholder {% endcomment %}
{{ field }}
{% if field.errors %}
  <p class="mt-1 text-xs text-red-500">{{ field.errors.0 }}</p>
{% endif %}
{% if field.help_text %}
  <p class="mt-1 text-xs text-gray-400">{{ field.help_text }}</p>
{% endif %}
```

#### `badge_status.html`
```django
{% comment %} Props: status, label {% endcomment %}
{% with colors=status|backoffice_status_color %}
  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {{ colors.0 }} {{ colors.1 }}">
    {{ label|default:status }}
  </span>
{% endwith %}
```
> **Implementar filtro** `backoffice_status_color` que mapee: activo → `bg-green-100 text-green-800`, inactivo → `bg-gray-100 text-gray-800`, pendiente → `bg-yellow-100 text-yellow-800`, etc.

#### `icon_link.html`
```django
{% comment %} Props: href, icon_class, aria_label, extra_classes {% endcomment %}
<a href="{{ href }}"
   class="inline-flex items-center justify-center w-8 h-8 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition {{ extra_classes }}"
   aria-label="{{ aria_label }}"
   title="{{ aria_label }}">
  <i class="{{ icon_class }}"></i>
</a>
```

#### `empty_state.html`
```django
{% comment %} Props: icon, title, description, action_url, action_text {% endcomment %}
<div class="text-center py-12">
  <div class="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
    <i class="{{ icon|default:'fas fa-inbox' }} text-gray-400 text-xl"></i>
  </div>
  <h3 class="text-lg font-medium text-gray-900 mb-1">{{ title }}</h3>
  {% if description %}<p class="text-sm text-gray-500 mb-4">{{ description }}</p>{% endif %}
  {% if action_url %}
    {% include 'backoffice/components/atoms/btn_primary.html' with href=action_url text=action_text %}
  {% endif %}
</div>
```

### 3.3 Componentes moleculares

#### `list_header.html`
```django
{% comment %} Props: title, create_url, create_text, filter_form? {% endcomment %}
<div class="flex items-center justify-between mb-6">
  {% include 'backoffice/components/atoms/page_title.html' with title=title %}
  {% if create_url %}
    {% include 'backoffice/components/atoms/btn_primary.html' with href=create_url text=create_text|default:'Crear' %}
  {% endif %}
</div>
{% if filter_form %}
  {% include 'backoffice/components/crud/list_filters.html' with form=filter_form %}
{% endif %}
```

#### `table_wrapper.html`
```django
{% comment %} Wrapper que estandariza el contenedor de tabla {% endcomment %}
<div class="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
  <table class="min-w-full divide-y divide-gray-200">
    {% block table_header %}{% endblock %}
    <tbody class="bg-white divide-y divide-gray-200">
      {% block table_body %}{% endblock %}
    </tbody>
  </table>
</div>
```

#### `table_header.html`
```django
<thead class="bg-gray-50">
  <tr>
    {% for column in columns %}
      <th scope="col"
          class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider
                 {% if forloop.last %}text-right{% endif %}">
        {{ column }}
      </th>
    {% endfor %}
  </tr>
</thead>
```

#### `confirm_modal.html`
```django
{% comment %} Props: title, message, confirm_url, confirm_text, cancel_url, extra_fields? {% endcomment %}
<div class="max-w-lg mx-auto mt-10">
  {% include 'backoffice/components/atoms/card.html' with padding='lg' %}
    <div class="text-center">
      <div class="w-12 h-12 mx-auto bg-red-100 rounded-full flex items-center justify-center mb-4">
        <i class="fas fa-exclamation-triangle text-red-600"></i>
      </div>
      <h2 class="text-xl font-bold text-gray-900 mb-2">{{ title }}</h2>
      <p class="text-sm text-gray-500 mb-6">{{ message }}</p>
      <form method="POST" action="{{ confirm_url }}">
        {% csrf_token %}
        {{ extra_fields }}
        <div class="flex justify-center gap-3">
          <a href="{{ cancel_url }}" class="...">Cancelar</a>
          <button type="submit" class="...">{{ confirm_text|default:'Confirmar' }}</button>
        </div>
      </form>
    </div>
  </div>
</div>
```

#### `dashboard_stat.html`
```django
{% comment %} Props: icon, value, label, link?, color_variant {% endcomment %}
<a {% if link %}href="{{ link }}"{% endif %}
   class="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition {% if link %}cursor-pointer{% endif %}">
  <div class="flex items-center gap-4">
    <div class="w-12 h-12 rounded-lg bg-brand-accent/10 flex items-center justify-center shrink-0">
      <i class="{{ icon }} text-brand-accent text-xl"></i>
    </div>
    <div>
      <p class="text-2xl font-bold text-gray-900">{{ value }}</p>
      <p class="text-sm text-gray-500">{{ label }}</p>
    </div>
  </div>
</a>
```

#### `form_card.html`
```django
{% comment %} Props: title, subtitle, form, submit_text, cancel_url {% endcomment %}
{% include 'backoffice/components/atoms/page_title.html' with title=title subtitle=subtitle %}
{% include 'backoffice/components/atoms/card.html' %}
  <form method="POST" {% if enctype %}enctype="{{ enctype }}"{% endif %}>
    {% csrf_token %}
    {% include 'backoffice/components/crud/form_fields.html' %}
    <div class="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
      {% if cancel_url %}
        {% include 'backoffice/components/atoms/btn_secondary.html' with href=cancel_url text='Cancelar' %}
      {% endif %}
      {% include 'backoffice/components/atoms/btn_primary.html' with type='submit' text=submit_text|default:'Guardar' %}
    </div>
  </form>
</div>
```

### 3.4 Mapa de refactor — CRUDs

#### Listados (16 templates)
Cada listado debe reemplazar su contenido por:
```django
{% include 'backoffice/components/molecules/list_header.html' with title=... create_url=... %}
{% include 'backoffice/components/molecules/table_wrapper.html' %}
  {% include 'backoffice/components/molecules/table_header.html' with columns=... %}
  <tbody>... rows with icon_link.html for actions ...</tbody>
</table>
{% include 'backoffice/components/crud/pagination.html' %}
```

| Template | Modelo | Acciones |
|----------|--------|----------|
| `hero_list.html` | HeroConfig | Editar, Desactivar/Activar, Papelera |
| `category_list.html` | Category | Editar, Eliminar |
| `collection_list.html` | Collection | Editar, Eliminar, Restaurar |
| `color_list.html` | Color | Editar, Eliminar |
| `product_list.html` | Product | Editar, Eliminar, Restaurar |
| `productcolor_list.html` | ProductColor | Editar, Eliminar |
| `productimage_list.html` | ProductImage | Editar, Eliminar |
| `size_list.html` | Size | Editar, Eliminar |
| `user_list.html` | User | Editar, Eliminar, Restaurar |
| `group_list.html` | Group | Editar, Eliminar |
| `order_list.html` | Order | Detalle, Cambiar estado |

#### Formularios (23 templates)
Cada formulario debe reemplazar por:
```django
{% include 'backoffice/components/molecules/form_card.html' with title=... form=form %}
```

**Templates prioritarios (tienen inline styles):**
1. `hero_form.html` — **11 inline styles**, preview de background-image con URL. Migrar: la URL como `style="background-image: url(...)"` controlada por el backend es aceptable, pero todo lo demás (font-family, border-radius, etc.) a utilidades.
2. `collection_style_form.html` — **9 inline styles** + `onclick="toggleAdvanced()"`. Migrar colores a `style="--color: ..."` y la función toggle a `collection-form-style.js` con `data-action`.
3. `product_form.html` — **alto (>50 atributos class)**, priorizar refactor.

#### Confirmaciones (29 templates)
Unificar todos los patrones de confirmación en `confirm_modal.html`:
```django
{% include 'backoffice/components/molecules/confirm_modal.html' with
  title='Eliminar producto'
  message='¿Estás seguro de eliminar este producto? Esta acción no se puede deshacer.'
  confirm_url=url
  cancel_url=url_list
%}
```

Las trashcans (`hero_trashcan`, `collection_trashcan`, `product_trashcan`, `user_trashcan`) deben usar `table_wrapper` + columnas estándar (nombre, fecha eliminación, acciones).

### 3.5 Mapas de refactor — Dashboards (8 templates)

| Template | Widgets |
|----------|---------|
| `admin_dashboard.html` | 4+ `dashboard_stat`, 2+ `chart_card`, `recent_list` |
| `admin_orders_dashboard.html` | 4+ `dashboard_stat`, `chart_card`, `recent_items_list` |
| `admin_products_dashboard.html` | 4+ `dashboard_stat`, stock info |
| `admin_users_dashboard.html` | 4+ `dashboard_stat`, `recent_items_list` |
| `delivery_dashboard.html` | 4+ `dashboard_stat` (métricas de entregas) |
| `importers_dashboard.html` | Cards de importación, botones de acción |
| `admin_config.html` | Formularios de configuración |
| `report_generator.html` | Filtros + botón generar |

**Acciones:**
- Reemplazar `stat_card`, `stat_card_big`, `stat_card_link` por `dashboard_stat` unificado
- `chart_card.html`: cambiar `style="height: 400px"` → `class="h-96"`
- Unificar `action_buttons_card.html` y `action_buttons_small.html` en uno con parámetro `size`

### 3.6 Reportes (5 templates)

Templates: `delivery_report.html`, `financial_report.html`, `orders_report.html`, `products_report.html`, `base_report.html`

Los reportes usan WeasyPrint que **no soporta Tailwind utilities**. Se mantiene CSS custom aquí, pero:
1. Mover colores hardcodeados a variables CSS `:root` en `base_report.html`
2. Quitar `style="padding: 40px"` inline → usar clase CSS del reporte
3. Asegurar que los `<th>` tengan `scope="col"`

### 3.7 Accesibilidad — Corrección masiva

**50+ `<th>` sin `scope="col"`** en todos los templates de listado y reporte:
```diff
- <th class="px-6 py-3 ...">{{ header }}</th>
+ <th scope="col" class="px-6 py-3 ...">{{ header }}</th>
```

Botones de solo ícono deben tener `aria-label`:
```diff
- <a href="..."><i class="fas fa-edit"></i></a>
+ <a href="..." aria-label="Editar" title="Editar"><i class="fas fa-edit"></i></a>
```

---

## 4. Parte C: PWA Delivery

### 4.1 Problemas críticos de arquitectura

| # | Problema | Impacto |
|---|----------|---------|
| 1 | CDN Tailwind (`https://cdn.tailwindcss.com`) es un script **bloqueante** de ~3MB. En una PWA offline-first, falla si no está cacheado. | **Alto** — la app no carga offline |
| 2 | `offline.html` carga CDN + `static/css/tailwind.css` (archivo que no existe) | **Alto** — doble carga innecesaria |
| 3 | Configuración inline `window.ZICADA` en `<head>` bloquea el parser | **Medio** |
| 4 | Font Awesome desde CDN — igual dependencia de red | **Medio** |
| 5 | Sin `display=swap` en Google Fonts | **Bajo** — FOIT |

#### Decisión estratégica para CSS en PWA

**Opción recomendada:** Precompilar un archivo `static/css/tailwind-pwa.css` con solo las clases usadas en los templates del delivery (auditar con `npx @tailwindcss/cli -i src.css -o static/css/tailwind-pwa.css --minify`). Esto elimina la dependencia de red y garantiza offline.

> Alternativa (si se prefiere mantener CDN): Cachear `cdn.tailwindcss.com` con estrategia `cache-first` en el Service Worker, pero la experiencia offline en el primer uso será deficiente.

**Acción inmediata:**
1. `offline.html`: eliminar `<script src="{% static 'css/tailwind.css' %}"></script>` (no existe) y el CDN duplicado
2. Usar el mismo CSS que el resto de la PWA
3. Cambiar botón de `bg-blue-600` a `bg-black` (identidad visual)

### 4.2 Layout base — `base_pwa.html`

#### Estructura post-refactor
```django
<body class="bg-gray-50 font-sans antialiased">
  {% include 'components/theme.html' %}
  {% include 'delivery/components/offline_indicator.html' %}
  <a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:bg-black focus:text-white focus:p-2 focus:z-50">Saltar al contenido</a>
  <div class="flex flex-col h-screen">
    {% block header %}
      {% include 'delivery/components/header_simple.html' %}
    {% endblock %}
    <main id="main-content" class="flex-1 overflow-y-auto pb-24" tabindex="-1">
      <div class="container mx-auto px-4 py-4">
        {% block content %}{% endblock %}
      </div>
    </main>
    {% block bottom_nav %}
      {% include 'delivery/components/bottom_nav.html' %}
    {% endblock %}
  </div>
  {% block extra_js %}{% endblock %}
</body>
```

**Cambios:**
- Mover el `skip-link` inline a clases sr-only + focus
- Cargar scripts con `defer` al final del body
- Mover `window.ZICADA` a un archivo `static/js/delivery/config.js` cargado con `defer`
- Mover SW registration a `static/js/delivery/sw-init.js`

### 4.3 Componentes atómicos — Delivery

Crear en `apps/delivery/templates/delivery/components/atoms/`.

#### `btn_primary.html`
```django
<button type="{{ type|default:'button' }}"
  class="w-full bg-black text-white py-3 rounded-xl font-semibold
         hover:bg-gray-900 active:scale-[0.98]
         transition-all duration-150
         focus:outline-hidden focus:ring-2 focus:ring-black focus:ring-offset-2
         disabled:opacity-50 disabled:cursor-not-allowed
         {{ extra_classes }}">
  {{ text }}
</button>
```

#### `btn_secondary.html`
```django
<button class="w-full bg-gray-100 text-gray-700 py-3 rounded-xl font-medium
               hover:bg-gray-200 active:scale-[0.98] transition-all
               focus:outline-hidden focus:ring-2 focus:ring-gray-400">
  {{ text }}
</button>
```

#### `btn_danger.html`
```django
<button class="w-full bg-red-600 text-white py-3 rounded-xl font-semibold
               hover:bg-red-700 active:scale-[0.98] transition-all">
  {{ text }}
</button>
```

#### `btn_success.html`
```django
<button class="w-full bg-green-600 text-white py-3 rounded-xl font-semibold
               hover:bg-green-700 active:scale-[0.98] transition-all">
  {{ text }}
</button>
```

#### `btn_warning.html`
```django
<button class="w-full bg-yellow-500 text-white py-3 rounded-xl font-semibold
               hover:bg-yellow-600 active:scale-[0.98] transition-all">
  {{ text }}
</button>
```

#### `input_text.html`
```django
<input type="{{ type|default:'text' }}" name="{{ name }}" placeholder="{{ placeholder }}"
  class="w-full border border-gray-300 rounded-lg px-3 py-2
         focus:outline-hidden focus:ring-2 focus:ring-black focus:border-transparent
         transition {{ extra_classes }}"
  value="{{ value|default:'' }}">
```

#### `badge_status.html`
```django
{% comment %} Mapeo: listo → yellow, en_camino → blue, entregado → green, cancelado → red, default → gray {% endcomment %}
{% with palette=status|delivery_status_color %}
  <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium {{ palette.bg }} {{ palette.text }}">
    <i class="fas fa-circle text-[0.5rem] mr-1.5 {{ palette.dot }}"></i>
    {{ label|default:status }}
  </span>
{% endwith %}
```

> **Implementar filtro** `delivery_status_color` que mapee los estados. Debe ser la **única fuente de verdad** para colores de estado, usada también en `orders.js`.

#### `badge_payment.html`
```django
{% with palette=payment_status|delivery_payment_color %}
  <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium {{ palette.bg }} {{ palette.text }}">
    {% if payment_status == 'pending' %}Pago pendiente{% elif payment_status == 'paid' %}Pagado{% else %}Pago en línea{% endif %}
  </span>
{% endwith %}
```

### 4.4 Componentes moleculares — Delivery

#### `order_card.html`
```django
{% comment %} Props: order (object con status, payment_status, total, items_count, address, id) {% endcomment %}
<a href="{% url 'delivery:order_detail' order.id %}"
   class="block bg-white rounded-xl shadow-sm hover:shadow-md active:scale-[0.98] transition-all overflow-hidden mb-3">
  <div class="p-4">
    <div class="flex items-start justify-between mb-2">
      <div class="min-w-0 flex-1 mr-2">
        <h3 class="font-semibold text-gray-900 truncate">Pedido #{{ order.id }}</h3>
        <p class="text-xs text-gray-500 truncate mt-0.5">{{ order.address }}</p>
      </div>
      {% include 'delivery/components/atoms/badge_status.html' with status=order.status %}
    </div>
    <div class="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-500">{{ order.items_count }} productos</span>
        {% include 'delivery/components/atoms/badge_payment.html' with payment_status=order.payment_status %}
      </div>
      <span class="text-lg font-bold text-gray-900">${{ order.total }}</span>
    </div>
  </div>
</a>
```
> **Importante:** El `orders.js` que renderiza pedidos dinámicamente debe generar **exactamente el mismo markup** que este componente. Se recomienda extraer un helper JS que construya el HTML usando string templates con las mismas clases.

#### `section_card.html`
```django
{% comment %} Props: title, icon, body, extra_classes {% endcomment %}
<div class="bg-white rounded-xl shadow-sm overflow-hidden mb-6 {{ extra_classes }}">
  <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-2">
    {% if icon %}<i class="{{ icon }} text-gray-500"></i>{% endif %}
    <h2 class="font-semibold text-gray-900 text-sm">{{ title }}</h2>
  </div>
  <div class="p-4">
    {{ body }}
  </div>
</div>
```

#### `modal_base.html`
```django
{% comment %} Props: id, title, body, footer {% endcomment %}
<div id="{{ id }}"
     class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4
            opacity-0 invisible transition-all duration-300"
     role="dialog" aria-modal="true" aria-labelledby="{{ id }}-title">
  <div class="bg-white rounded-xl max-w-sm w-full shadow-xl max-h-[90vh] overflow-y-auto">
    <div class="px-6 py-4 border-b border-gray-200">
      <h3 id="{{ id }}-title" class="font-semibold text-gray-900">{{ title }}</h3>
    </div>
    <div class="px-6 py-4">
      {{ body }}
    </div>
    {% if footer %}
      <div class="px-6 py-4 border-t border-gray-200 flex gap-3">
        {{ footer }}
      </div>
    {% endif %}
  </div>
</div>
```

#### `fixed_action_bar.html`
```django
{% comment %} Props: buttons (contiene los botones), extra_classes {% endcomment %}
<div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 z-40 {{ extra_classes }}">
  <div class="flex gap-3 max-w-lg mx-auto">
    {{ buttons }}
  </div>
</div>
```

#### `empty_state.html`
```django
{% comment %} Props: icon, title, description, action_url, action_text {% endcomment %}
<div class="text-center py-16 px-4">
  <div class="w-24 h-24 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
    <i class="{{ icon|default:'fas fa-box-open' }} text-gray-400 text-3xl"></i>
  </div>
  <h3 class="text-lg font-semibold text-gray-900 mb-1">{{ title }}</h3>
  {% if description %}<p class="text-sm text-gray-500 mb-6">{{ description }}</p>{% endif %}
  {% if action_url %}
    <a href="{{ action_url }}" class="inline-block bg-black text-white px-6 py-3 rounded-xl font-semibold hover:bg-gray-900 transition">
      {{ action_text }}
    </a>
  {% endif %}
</div>
```

#### `install_banner.html`
```django
{% comment %} Props: platform (android|ios), on_dismiss {% endcomment %}
<div class="bg-gradient-to-r from-brand-accent via-gray-900 to-black text-white rounded-xl p-4 mb-6 shadow-md relative overflow-hidden">
  {# decorative blur circles #}
  <div class="absolute -top-4 -right-4 w-20 h-20 bg-white/5 rounded-full blur-xl"></div>
  <div class="absolute -bottom-4 -left-4 w-16 h-16 bg-white/5 rounded-full blur-xl"></div>
  <div class="relative">
    <p class="text-sm font-semibold mb-1">
      {% if platform == 'android' %}Instala la app{% else %}Añade a la pantalla de inicio{% endif %}
    </p>
    <p class="text-xs text-white/80 mb-3">
      {% if platform == 'android' %}Toca el menú y selecciona "Instalar app"{% else %}Toca el botón compartir y "Añadir a pantalla de inicio"{% endif %}
    </p>
    <button data-dismiss-install-banner
            class="text-xs text-white/70 hover:text-white underline underline-offset-2 transition"
            aria-label="Cerrar banner de instalación">
      Cerrar
    </button>
  </div>
</div>
```

#### `page_header.html` (unifica header_simple + header_dashboard)
```django
{% comment %} Props: type(simple|dashboard), title, back_url?, extra_classes {% endcomment %}
<header class="bg-white shadow-sm sticky top-0 z-40 {{ extra_classes }}">
  <div class="flex items-center justify-between px-4 py-3">
    <div class="flex items-center min-w-0">
      {% if back_url %}
        <a href="{{ back_url }}" class="mr-3 text-gray-500 hover:text-gray-700 transition" aria-label="Volver">
          <i class="fas fa-arrow-left text-lg"></i>
        </a>
      {% endif %}
      <h1 class="font-semibold text-gray-900 truncate {% if type == 'dashboard' %}text-lg{% else %}text-base{% endif %}">
        {{ title }}
      </h1>
    </div>
    <div class="flex items-center gap-2 shrink-0">
      {% if type == 'dashboard' %}
        <a href="{% url 'delivery:summary' %}" class="text-gray-500 hover:text-gray-700 p-2 transition" aria-label="Resumen diario">
          <i class="fas fa-chart-simple"></i>
        </a>
      {% endif %}
      <form method="POST" action="{% url 'delivery:logout' %}" class="inline">
        {% csrf_token %}
        <button type="submit" class="text-red-600 hover:text-red-700 text-sm font-medium transition" aria-label="Cerrar sesión">
          <i class="fas fa-right-from-bracket"></i>
        </button>
      </form>
    </div>
  </div>
</header>
```

#### `offline_indicator.html` (refactor del existente)
```django
<div id="offline-indicator"
     class="fixed top-0 left-0 right-0 bg-red-500 text-white text-center py-2 text-sm z-50 hidden"
     role="alert">
  <div class="flex items-center justify-center gap-2">
    <i class="fas fa-wifi-slash"></i>
    <span>Sin conexión — los datos pueden no estar actualizados</span>
    <button data-dismiss-offline
            class="ml-2 text-white/80 hover:text-white transition"
            aria-label="Cerrar indicador offline">
      <i class="fas fa-times"></i>
    </button>
  </div>
</div>
```

### 4.5 Templates a refactorizar

#### `dashboard.html`
- Usar `page_header.html` con `type="dashboard"`
- Usar `stat_card.html` atómico para los 3 stats (pendientes, activos, completados)
- Usar `section_card.html` para "Pedidos activos"
- Usar `install_banner.html` (Android e iOS con el mismo componente, distinto parámetro)
- Usar `order_card.html` para los pedidos activos
- Eliminar gradiente inline duplicado para Android/iOS
- Eliminar lógica de color de pago inline (debe ir en `badge_payment.html`)

#### `login.html`
- Extraer ~80 líneas de inline JS a `static/js/delivery/login.js`
- Mantener funcionalidad: toggle de visibilidad de contraseña, validación de formulario, prevención de doble envío
- Usar componentes atómicos `input_text.html` y `btn_primary.html`

#### `orders/list.html`
- Usar `page_header.html` con `type="simple"` y `back_url`
- Usar `empty_state.html` cuando no haya pedidos
- Usar `order_card.html` para server-render inicial
- Mantener filtros horizontales (scroll horizontal con `flex overflow-x-auto`)
- **Sincronizar JS:** `orders.js` debe generar el mismo HTML que `order_card.html`
- Estandarizar filtros: reemplazar `bg-black text-white` / `bg-gray-100 text-gray-700` toggle por data-attributes manejados por una función reusable

#### `orders/detail.html`
- Usar `page_header.html` con `type="simple"`, `back_url` a la lista
- Usar `section_card.html` para: Información del pedido, Productos, Incidencias
- Usar `badge_status.html` y `badge_payment.html`
- Usar `modal_base.html` para modal de pago y modal de incidencia
- Usar `fixed_action_bar.html` con botones de acción
- **Corregir z-index:** la action bar debe ser `z-40` (no `z-50` para no tapar modales)
- **Corregir pb-24 duplicado:** solo el `<main>` del layout base debe tener `pb-24`

#### `summary/daily.html`
- Usar `page_header.html` con `type="simple"`, `back_url`
- Usar `stat_card.html` para montos y conteos
- Usar `section_card.html` para lista de entregas completadas

#### `incidences/form.html`
- Usar `page_header.html` con `type="simple"`, `back_url`
- Usar `section_card.html` para el formulario
- Usar `fixed_action_bar.html` para el botón enviar
- Reemplazar `radio-custom` + `incidence-card` por `appearance-none` + `peer-checked:` de Tailwind:
  ```django
  <label class="block border-2 rounded-xl p-4 cursor-pointer transition
                border-gray-200 has-checked:border-black has-checked:bg-gray-50">
    <input type="radio" name="incidence_type" value="{{ val }}" class="appearance-none peer">
    <div class="flex items-center gap-3">
      <div class="w-5 h-5 rounded-full border-2 border-gray-300
                  peer-checked:border-black peer-checked:bg-black
                  peer-checked:ring-2 peer-checked:ring-black peer-checked:ring-offset-2"></div>
      <span>{{ label }}</span>
    </div>
  </label>
  ```

#### `offline.html`
- Quitar CDN duplicado y `static/css/tailwind.css`
- Cargar el mismo CSS que `base_pwa.html`
- Reemplazar botón `bg-blue-600` por `{% include 'delivery/components/atoms/btn_primary.html' with text='Reintentar' %}`
- Reemplazar `onclick="window.location.reload()"` por `id="retry-btn"` + JS externo con `addEventListener`

### 4.6 Correcciones de inconsistencias

| # | Problema | Templates | Corrección |
|---|----------|-----------|------------|
| 1 | `offline.html` usa `bg-blue-600` para el único botón | `offline.html` | Usar `btn_primary.html` (negro) |
| 2 | `payment_modal` usa `py-3 rounded-xl`; `incidence_modal` usa `py-2 rounded-lg` | Ambos modales | Estandarizar a `py-3 rounded-xl` vía `modal_base.html` |
| 3 | `payment_modal` sin `max-h-[90vh]`; `incidence_modal` sí | Ambos modales | `modal_base.html` incluye `max-h-[90vh] overflow-y-auto` |
| 4 | `bottom_nav` z-40, action bar z-40/50 | `bottom_nav.html`, `detail.html`, `form.html` | Nav z-40, action bar z-40, modales z-50 |
| 5 | `pb-24` duplicado en layout + detail | `base_pwa.html`, `orders/detail.html` | Solo el layout aplica `pb-24` |
| 6 | `order_card.html` sin feedback táctil | `order_card.html` | Añadir `active:scale-[0.98]` |
| 7 | `header_dashboard` logout gris; `header_simple` logout rojo | Ambos headers | Estandarizar logout rojo en `page_header.html` |
| 8 | Payment badge: server dice "Pago pendiente"/"Pagado"; JS dice "Pago en línea" | `order_card.html`, `orders.js`, `dashboard.html` | Unificar en `badge_payment.html` |
| 9 | Focus ring inconsistente: `focus:ring-black` vs `focus:ring-gray-400` vs sin `ring-offset-2` | Múltiples templates | Estandarizar en componentes atómicos |

### 4.7 PWA — JS crítico a refactorizar

#### `static/js/delivery/orders.js`
**Problema:** Genera HTML de tarjetas de pedido con clases inline. Si se cambia un componente, el JS queda desactualizado.

**Solución:** Extraer un **helper de componentes JS** en `static/js/delivery/components.js`:
```js
// components.js — Genera HTML consistente con los templates Django
const DeliveryComponents = {
  orderCard(order) {
    return `
      <a href="/delivery/orders/${order.id}/"
         class="block bg-white rounded-xl shadow-sm hover:shadow-md active:scale-[0.98] transition-all overflow-hidden mb-3">
        ... (mismo markup que order_card.html)
      </a>
    `;
  },
  statusBadge(status, label) {
    const colors = {
      listo: { bg: 'bg-yellow-100', text: 'text-yellow-800', dot: 'text-yellow-500' },
      en_camino: { bg: 'bg-blue-100', text: 'text-blue-800', dot: 'text-blue-500' },
      entregado: { bg: 'bg-green-100', text: 'text-green-800', dot: 'text-green-500' },
      cancelado: { bg: 'bg-red-100', text: 'text-red-800', dot: 'text-red-500' },
    };
    const c = colors[status] || { bg: 'bg-gray-100', text: 'text-gray-800', dot: 'text-gray-500' };
    return `<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}">
      <i class="fas fa-circle text-[0.5rem] mr-1.5 ${c.dot}"></i>${label || status}</span>`;
  },
  // ... más helpers
};
```

**En `orders.js`:**
- Reemplazar toda construcción de HTML por `DeliveryComponents.orderCard(order)`
- Mapeo de colores de estado: debe ser idéntico al filtro `delivery_status_color` de Django

#### `static/js/delivery/base.js`
- Mantener manejo de eventos `online`/`offline` para el indicador
- Estandarizar toggle: `el.classList.remove('hidden')` ↔ `el.classList.add('hidden')`
- Reemplazar lógica de modal (`.classList.add('active')`) por: `modal.classList.remove('opacity-0', 'invisible')` y `modal.classList.add('opacity-100', 'visible')`

#### `static/js/delivery/login.js` (nuevo)
- Extraer de `login.html`
- Password toggle: data-attribute `data-toggle-password`
- Validación: `data-validate` en el formulario
- Prevención doble envío: deshabilitar botón submit después del primer click

#### `static/js/delivery/sw-init.js` (nuevo)
- Extraer Service Worker registration de `base_pwa.html`
- Cachear `cdn.tailwindcss.com` con estrategia `cache-first` (solo si se mantiene CDN)

#### Patrones de clase JS — documentar en `AGENTS.md`
```markdown
## Patrones JS ↔ Tailwind (PWA Delivery)

- **Modal toggle:** `modal.classList.toggle('opacity-0'); modal.classList.toggle('invisible'); modal.classList.toggle('opacity-100'); modal.classList.toggle('visible');`
- **Filter button:** estado activo = `bg-black text-white rounded-full`; inactivo = `bg-gray-100 text-gray-700 rounded-full`
- **Order filter:** botón activo se togglea con la función `toggleFilter` en `orders.js`
- **Offline indicator:** `offlineIndicator.classList.toggle('hidden')` en eventos `online`/`offline`
```

---

## 5. Estáticos y JavaScript — Refactor global

### 5.1 CSS — Archivos a eliminar/consolidar

| Archivo | Acción | Justificación |
|---------|--------|---------------|
| `static/css/custom.css` (vacío) | **Eliminar** + quitar `<link>` de `base.html` | Solicitud HTTP innecesaria |
| `static/css/products/product_detail.css` | **Migrar** a utilidades y **eliminar** | Duplica Tailwind |
| `static/css/orders/checkout.css` | **Migrar** a utilidades y **eliminar** | Idéntico a cart_detail.css |
| `static/css/orders/cart_detail.css` | **Migrar** a utilidades y **eliminar** | Idéntico a checkout.css |
| `static/css/delivery/main.css` | **Reducir** al mínimo | Mantener solo: `* {-webkit-tap-highlight-color: transparent;}`, `@keyframes`, reglas `@page` WeasyPrint |
| `static/css/tailwind-pwa.css` | **Crear** (precompilado) | Reemplazar CDN en PWA |

### 5.2 JS — Archivos a crear/eliminar

| Archivo | Acción | Justificación |
|---------|--------|---------------|
| `static/js/main.js` (vacío) | **Eliminar** + quitar `<script>` | Sin código |
| `static/js/delivery/login.js` | **Crear** | Extraer inline script de `login.html` |
| `static/js/delivery/sw-init.js` | **Crear** | Extraer SW registration de `base_pwa.html` |
| `static/js/delivery/components.js` | **Crear** | Helpers de componentes JS sincronizados con templates |

### 5.3 Estrategia de carga de scripts

| Layout | Cambio |
|--------|--------|
| `base.html` | Mover scripts al final de `<body>` con `defer` |
| `backoffice_base.html` | Mover ApexCharts/SortableJS a `{% block extra_js %}` de cada página |
| `base_pwa.html` | Mover inline config a `sw-init.js` + `defer` |
| `base_report.html` | Sin cambios (no usa JS) |

### 5.4 Estandarización de modales JS

Actualmente hay **3 implementaciones de modal toggle**:
1. `header.js`: toggle `hidden`/`flex` en overlay + search
2. `cart.js`: toggle `translate-x-full`/`translate-x-0` para slide-over
3. `delivery/order-detail.js`: toggle clase `active` (depende de CSS custom)
4. `confirm-modal.js`: replace `className` completo de botones

**Acción:** Documentar en AGENTS.md y crear función reusable:
```js
function toggleModal(modalId, show) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.classList.toggle('opacity-0', !show);
  modal.classList.toggle('invisible', !show);
  modal.classList.toggle('opacity-100', show);
  modal.classList.toggle('visible', show);
  document.body.classList.toggle('overflow-hidden', show);
}
```

---

## 6. Roadmap de Ejecución

### Fase 1: Fundamentos (sin riesgo — 1 sesión)
- [ ] Crear `apps/core/templates/components/theme.html` con `@theme`
- [ ] Incluir en los 3 layouts base
- [ ] Eliminar `<script>tailwind.config</script>` inline de los 3 layouts
- [ ] Eliminar `custom.css` vacío y su `<link>` de `base.html`
- [ ] Eliminar `main.js` vacío y su `<script>` de `base.html`
- [ ] Añadir `defer` a scripts restantes en layouts

### Fase 2: Componentes atómicos Backoffice (1-2 sesiones)
- [ ] Crear `backoffice/components/atoms/btn_primary.html`
- [ ] Crear `backoffice/components/atoms/btn_secondary.html`
- [ ] Crear `backoffice/components/atoms/btn_danger.html`
- [ ] Crear `backoffice/components/atoms/btn_danger_text.html`
- [ ] Crear `backoffice/components/atoms/card.html`
- [ ] Crear `backoffice/components/atoms/page_title.html`
- [ ] Crear `backoffice/components/atoms/form_label.html`
- [ ] Crear `backoffice/components/atoms/form_input.html`
- [ ] Crear `backoffice/components/atoms/badge_status.html`
- [ ] Crear `backoffice/components/atoms/icon_link.html`
- [ ] Crear `backoffice/components/atoms/empty_state.html`

### Fase 3: Componentes moleculares Backoffice (1 sesión)
- [ ] Crear `backoffice/components/molecules/list_header.html`
- [ ] Crear `backoffice/components/molecules/table_wrapper.html`
- [ ] Crear `backoffice/components/molecules/table_header.html`
- [ ] Crear `backoffice/components/molecules/confirm_modal.html`
- [ ] Crear `backoffice/components/molecules/dashboard_stat.html`
- [ ] Crear `backoffice/components/molecules/form_card.html`

### Fase 4: Refactor CRUDs Backoffice (3-4 sesiones)
- [ ] Refactorizar **listados** (16 templates): reemplazar con `list_header + table_wrapper + table_header`
- [ ] Añadir `scope="col"` a todos los `<th>` en tablas
- [ ] Añadir `aria-label` a botones de ícono
- [ ] Refactorizar **formularios** (23 templates): usar `form_card.html`
- [ ] Migrar inline styles de `hero_form.html` y `collection_style_form.html`
- [ ] Refactorizar **confirmaciones** (29 templates): usar `confirm_modal.html`
- [ ] Refactorizar **dashboards** (8 templates): usar `dashboard_stat.html`, unificar widgets

### Fase 5: Refactor Reportes (1 sesión)
- [ ] Centralizar colores en variables `:root` en `base_report.html`
- [ ] Eliminar `style="padding: 40px"` inline
- [ ] Añadir `scope="col"` a `<th>`

### Fase 6: PWA Delivery — CSS y Layout (1 sesión)
- [ ] Decidir: precompilar `tailwind-pwa.css` o cachear CDN en SW
- [ ] Crear / configurar el archivo CSS resultante
- [ ] Corregir `offline.html`: eliminar CDN duplicado, botón azul → negro
- [ ] Mover `window.ZICADA` a `sw-init.js` con `defer`
- [ ] Mover SW registration a `sw-init.js`
- [ ] Extraer login inline JS a `login.js`

### Fase 7: PWA Delivery — Componentes (2 sesiones)
- [ ] Crear `delivery/components/atoms/*` (btn_primary, btn_secondary, btn_danger, btn_success, btn_warning, input_text, badge_status, badge_payment)
- [ ] Crear `delivery/components/molecules/*` (order_card, section_card, modal_base, fixed_action_bar, empty_state, install_banner, page_header)
- [ ] Refactorizar `orders.js`: extraer `DeliveryComponents` helper
- [ ] Refactorizar `dashboard.html`, `orders/list.html`, `orders/detail.html`, `summary/daily.html`, `incidences/form.html`
- [ ] Corregir z-index, pb-24 duplicado, modales, colores de logout

### Fase 8: Calidad y validación (1 sesión)
- [ ] Verificar que no queden `<script>tailwind.config</script>` en ningún template
- [ ] Verificar que no queden `style="..."` inline (excepto casos controlados)
- [ ] Verificar que no queden `onclick="..."` inline
- [ ] Verificar que todos los `<th>` tengan `scope`
- [ ] Verificar que botones de ícono tengan `aria-label`
- [ ] Ejecutar `DJANGO_SETTINGS_MODULE=config.settings_test pytest apps/ -v` y arreglar roturas
- [ ] Revisar visualmente: backoffice listados, formularios, dashboards; PWA dashboard, listado, detalle

---

## Apéndice A: Mapeo de archivos CSS custom → Utilidades Tailwind

### `product_detail.css` → qué reemplazar
| Clase CSS | Reemplazo Tailwind |
|-----------|-------------------|
| `.product-gallery-thumb` | `transition-all duration-200 ease cursor-pointer border-2 border-transparent grayscale-[0.3] hover:grayscale-0 hover:scale-105 hover:shadow-lg` |
| `.quantity-input` | `w-[60px] text-center border border-gray-300 rounded-lg p-2 font-medium` |
| `.quantity-btn` | `w-7 h-7 bg-gray-100 rounded-full hover:bg-gray-200 transition text-gray-600 font-medium flex items-center justify-center` |
| `.variant-btn` | `px-4 py-2 rounded-lg border text-sm font-medium transition data-[state=selected]:bg-gray-900 data-[state=selected]:text-white` |
| `.color-preview` | `w-8 h-8 rounded-full border-2 border-gray-300 transition hover:scale-110` |

### `checkout.css` + `cart_detail.css` → qué reemplazar
| Clase CSS | Reemplazo Tailwind |
|-----------|-------------------|
| `.cart-item` | `bg-white rounded-2xl p-4 mb-4 shadow-sm transition hover:shadow-md hover:-translate-y-0.5` |
| `.quantity-btn` | `w-8 h-8 flex items-center justify-center bg-gray-100 rounded-full font-semibold hover:bg-gray-200 hover:scale-105 transition` |
| `.remove-btn` | `p-2 rounded-lg transition hover:bg-red-50 hover:text-red-600` |
| `.summary-card` | `sticky top-24 bg-white rounded-2xl shadow-lg p-6` |
| `.form-label` | `block text-sm font-semibold text-gray-700 mb-2` |

### `delivery/main.css` → qué mantener/eliminar
| Regla | Acción |
|-------|--------|
| `.card-hover:active { transform: scale(0.98) }` | **Eliminar** → usar `active:scale-[0.98]` directamente |
| `.modal { transition: opacity 0.3s, visibility 0.3s }` | **Eliminar** → usar `transition-all duration-300` en clases |
| `.modal.active { opacity: 1; visibility: visible }` | **Eliminar** → toggle `opacity-100 visible` desde JS |
| `* { -webkit-tap-highlight-color: transparent }` | **Mantener** (no hay utility) |
| `button:focus-visible { outline: 2px solid black; outline-offset: 2px }` | **Eliminar** → usar `focus-visible:outline-2 focus-visible:outline-black focus-visible:outline-offset-2` |
| `.pull-indicator { transition: transform 0.3s ease }` | **Mantener** (animación pull-to-refresh no tiene utility directa) |

---

## Apéndice B: Diseño de filtro `delivery_status_color`

```python
# apps/delivery/templatetags/delivery_tags.py
from django import template

register = template.Library()

STATUS_COLORS = {
    'listo': {'bg': 'bg-yellow-100', 'text': 'text-yellow-800', 'dot': 'text-yellow-500'},
    'en_camino': {'bg': 'bg-blue-100', 'text': 'text-blue-800', 'dot': 'text-blue-500'},
    'entregado': {'bg': 'bg-green-100', 'text': 'text-green-800', 'dot': 'text-green-500'},
    'cancelado': {'bg': 'bg-red-100', 'text': 'text-red-800', 'dot': 'text-red-500'},
}

@register.filter
def delivery_status_color(status):
    return STATUS_COLORS.get(status, {'bg': 'bg-gray-100', 'text': 'text-gray-800', 'dot': 'text-gray-500'})
```

El helper JS `DeliveryComponents.statusBadge()` en `components.js` debe usar **exactamente el mismo mapeo** para mantener consistencia server-side ↔ client-side.

---

## Apéndice C: Resumen de eliminación de archivos

| Archivo | Fase | Acción |
|---------|------|--------|
| `static/css/custom.css` | 1 | Eliminar |
| `static/js/main.js` | 1 | Eliminar |
| `static/css/products/product_detail.css` | 5 (post-reforma cliente) | Eliminar |
| `static/css/orders/checkout.css` | 5 (post-reforma cliente) | Eliminar |
| `static/css/orders/cart_detail.css` | 5 (post-reforma cliente) | Eliminar |
| `static/css/delivery/main.css` | 6 | Reducir (mantener solo tap-highlight + @page) |

---

*Fin del documento. Este plan debe ser ejecutado por fases según el roadmap del Apéndice E.*
