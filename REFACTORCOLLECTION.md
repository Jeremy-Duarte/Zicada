# REFACTORCOLLECTION.md

Refactor de colecciones: navegación por **imagen interactiva** con zonas clicleables que redirigen a productos.

Branch: `planning-frontend`

---

## Objetivo

Transformar el flujo de colecciones:

```
Collection List (collections_list.html)
        │
        ▼  (clic en la colección)
Página de imagen interactiva (NUEVO)
        │
        ├─ zonas clicleables → product detail (con ?color=pc_id)
        │
        └─ si no hay interactive_background → error/obligar a configurar
```

La relación `Product ↔ Collection` **no cambia**. Solo cambia la navegación: en vez de un grid de productos, el usuario navega haciendo clic sobre zonas rectangulares delimitadas sobre una imagen.

---

## Decisiones de diseño (YA acordadas)

1. **Forzar interactiva**: todas las colecciones deben tener `interactive_background`. Si no lo tienen, el flujo público debe impedir el acceso (redirect a la home / mensaje) y el CRUD debe obligar a cargarlo.
2. **Editor visual completo en fase 1**: canvas + vanilla JS con draw/drag/resize. Sin librerías externas.
3. **Zonas linkean a `ProductColor`** (no a `Product` genérico): el link incluye `?color=pc_id` para preseleccionar el color exacto que aparece en la foto.
4. **Coordenadas en porcentajes (0-100)**: responsive nativo sin JS en el display público.
5. **Display público sin librerías**: `<img>` + `<a>` con `position: absolute` y `left/top/width/height` en %.

---

## Fase 1 — Modelo y migración

### 1.1 Campo nuevo en `Collection` (`apps/products/models.py`)

```python
interactive_background = models.ImageField(
    upload_to='collections/interactive/', blank=True, null=True
)
```

### 1.2 Nuevo modelo `InteractiveZone`

```python
class InteractiveZone(BaseAuditModel):
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE,
        related_name='interactive_zones'
    )
    product_color = models.ForeignKey(
        ProductColor, on_delete=models.CASCADE,
        related_name='interactive_zones'
    )
    x = models.DecimalField(max_digits=5, decimal_places=2)  # % izquierda (0-100)
    y = models.DecimalField(max_digits=5, decimal_places=2)  # % arriba (0-100)
    width = models.DecimalField(max_digits=5, decimal_places=2)   # % ancho (0-100)
    height = models.DecimalField(max_digits=5, decimal_places=2)  # % alto (0-100)
    label = models.CharField(max_length=100, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']
```

Hereda de `BaseAuditModel` → soft-delete, `created_by/updated_by`, `objects` (activos).

### 1.3 Migración

```bash
python manage.py makemigrations products
python manage.py migrate
```

---

## Fase 2 — Display público (HTML nativo)

### 2.1 Vista `CollectionDetailView` (`apps/products/views.py`)

Modificar:
- Si `collection.interactive_background` existe Y tiene `interactive_zones` → renderizar `collection_interactive.html`.
- Si no tiene `interactive_background` → como es "forzar interactiva", lanzar `Http404` (o redirect) porque la colección no está lista. Mantener el grid actual SOLO como fallback de desarrollo si hiciera falta.
- `get_queryset`: `prefetch_related('interactive_zones', 'interactive_zones__product_color', 'interactive_zones__product_color__product')`.

### 2.2 Template `collection_interactive.html` (NUEVO)

```html
{% extends "layouts/base.html" %}
{% block title %}{{ collection.name }} - Zicada{% endblock %}

{% block content %}
<div class="bg-black text-white font-poppins">
  <div class="relative w-full">
    <img src="{{ collection.interactive_background.url }}"
         alt="{{ collection.name }}" class="w-full h-auto block">
    {% for zone in zones %}
    <a href="{% url 'products:product_detail' zone.product_color.product.slug %}?color={{ zone.product_color.pk }}"
       class="absolute block cursor-pointer transition-all duration-300
              hover:ring-2 hover:ring-white/80
              hover:shadow-[0_0_20px_rgba(255,255,255,0.3)]"
       style="left: {{ zone.x }}%; top: {{ zone.y }}%;
              width: {{ zone.width }}%; height: {{ zone.height }}%;"
       title="{{ zone.product_color.product.name }} - {{ zone.product_color.color.name }}">
    </a>
    {% endfor %}
  </div>
</div>
{% endblock %}
```

- Zonas vacías (`label` vacío) → `<a>` invisible pero clicable (hover lo revela).
- Imagen debe ocupar todo el ancho; altura proporcional (`h-auto`).

### 2.3 Link desde `collections_list.html`

El link actual:
```html
<a href="{% url 'products:collection_detail' collection.slug %}" ...>
```
Se queda igual (la URL `collection_detail` ahora renderiza la vista interactiva). No cambia nada en este template salvo que el target cambia internamente.

---

## Fase 3 — Backoffice: CRUD de zonas (editor visual)

### 3.1 URLs (`apps/products/urls.py`, en `admin_patterns`)

```python
path('colecciones/<int:pk>/zonas/', views.CollectionZoneEditorView.as_view(), name='collection_zones'),
path('colecciones/<int:pk>/zonas/api/', views.CollectionZoneAPIView.as_view(), name='collection_zones_api'),
path('colecciones/<int:pk>/zonas/<int:zone_pk>/api/', views.CollectionZoneDetailAPIView.as_view(), name='collection_zone_api_detail'),
```

### 3.2 Vistas (`apps/products/views.py`)

**`CollectionZoneEditorView`** (LoginRequired, staff/permisos):
- Context: `collection`, `interactive_background_url`, zonas existentes como JSON (`x, y, width, height, label, product_color_id`), y lista de `product_color` de la colección (`select_related` + `prefetch_related`).
- Template: `products/backoffice/collection_zone_editor.html`.

**`CollectionZoneAPIView`** (POST create, GET list):
- POST recibe JSON: `{x, y, width, height, product_color_id, label}`.
- Valida: coordenadas en [0,100], `product_color` pertenece a la colección.
- Retorna la zona creada como JSON con `id`.

**`CollectionZoneDetailAPIView`** (PUT update, DELETE delete):
- PUT recibe el JSON completo (incluye `id`).
- DELETE marca soft-delete (`zone.soft_delete(user=request.user)`) o hard-delete directo.
- Retorna `{status: ok}`.

Permisos: usar el mismo patrón de permisos de las demás vistas backoffice (staff / is_superuser según exista en el proyecto).

### 3.3 Template `collection_zone_editor.html` (NUEVO)

- Contenedor con la imagen interactiva.
- Canvas superpuesto para dibujar.
- Barra lateral/header con: botón "Guardar", botón "Nueva zona" (activa modo draw), lista de zonas existentes.
- Zonas se dibujan como rectángulos con color semitransparente + borde.
- Modal para asignar `ProductColor` (búsqueda por producto/color) a la zona creada/seleccionada.

### 3.4 JS `static/js/products/collection-zone-editor.js` (NUEVO)

Estado:
```js
const state = {
  zones: [],                 // [{id, x, y, width, height, label, product_color_id}]
  selectedZoneId: null,
  mode: 'select',            // 'select' | 'draw'
  imageNatural: {w, h},      // para calcular %
  canvas: {...}, displayScale, offsetX, offsetY,
  dirty: false,
};
```

Funciones:
- `init()`: carga imagen, configura canvas, dibuja zonas existentes.
- `drawZones()`: redibuja todo cada cambio.
- `hitTest(mouseX, mouseY)`: detecta zona o handle bajo el cursor.
- `startDraw(e)`: `mousedown` en modo 'draw' → fija punto inicial.
- `updateDraw(e)`: `mousemove` → actualiza rectángulo temporal.
- `finishDraw(e)`: `mouseup` → crea zona temporal, abre modal de producto.
- `startSelectDrag(e)`: `mousedown` sobre zona → mueve.
- `startResize(e, handle)`: `mousedown` sobre handle → redimensiona.
- `onMouseMove(e)` / `onMouseUp(e)`: dispatch según estado.
- `saveZones()`: calcula % desde píxeles (`px / natural * 100`), valida, POST/PUT a la API.
- `deleteZone(id)`: DELETE a la API.
- `openProductModal(zoneId)`: modal con búsqueda de `product_color`.

Conversión coordenadas (clave):
```js
// píxeles → porcentaje
pctX = (pixelX - offsetX) / displayedWidth * 100;
// porcentaje → píxeles (al dibujar)
pixelX = offsetX + (pctX / 100) * displayedWidth;
```

### 3.5 Formularios (`apps/products/forms.py`)

- `CollectionCreateForm` y `CollectionUpdateForm`: añadir `interactive_background` como **requerido** (`required=True`).
- `clean_interactive_background`: validar que sea imagen.

### 3.6 Admin (Django admin, `apps/products/admin.py`)

- Opcional: inline de `InteractiveZone` en `CollectionAdmin` para edición rápida por números.
- Importante: el editor principal es la página custom de zonas.

---

## Fase 4 — Acceso a zonas desde backoffice

- En `CollectionListView` (backoffice), añadir columna/acción "Zonas" con link a `collection_zones`.
- Link: `{% url 'products:collection_zones' collection.pk %}`.

---

## Validación de coordenadas

En `InteractiveZone.clean()`:
- `0 <= x <= 100`, `0 <= y <= 100`
- `x + width <= 100`, `y + height <= 100`
- `width > 0`, `height > 0`

En la API: repetir la misma validación antes de guardar.

---

## Optimizaciones ORM

- `CollectionZoneEditorView`: `collection.interactive_zones.select_related('product_color__product', 'product_color__color')`.
- `CollectionDetailView`: `prefetch_related('interactive_zones__product_color__product', 'interactive_zones__product_color__color')`.
- Lista de product_color para el modal: `collection.products.prefetch_related('product_colors__color', 'product_colors__product')`.

---

## Archivos

| Archivo | Acción |
|---------|--------|
| `apps/products/models.py` | + campo `interactive_background` en `Collection`; + modelo `InteractiveZone` |
| `apps/products/migrations/00XX_*.py` | NUEVO (makemigrations) |
| `apps/products/views.py` | + `CollectionZoneEditorView`, `CollectionZoneAPIView`, `CollectionZoneDetailAPIView`; modificar `CollectionDetailView` |
| `apps/products/urls.py` | + 3 rutas backoffice |
| `apps/products/forms.py` | `interactive_background` requerido en create/update |
| `apps/products/admin.py` | + inline `InteractiveZone` (opcional) |
| `apps/products/templates/products/collection_interactive.html` | NUEVO — página pública |
| `apps/products/templates/products/backoffice/collection_zone_editor.html` | NUEVO — editor canvas |
| `static/js/products/collection-zone-editor.js` | NUEVO — lógica del editor |
| `apps/products/views.py` → `CollectionListView` | + columna/acción "Zonas" |

---

## Verificación

```bash
# Migraciones
python manage.py makemigrations products && python manage.py migrate

# Tests
DJANGO_SETTINGS_MODULE=config.settings_test pytest apps/products/tests/ -v

# Servidor local
python manage.py runserver
```

Casos a probar:
1. Colección con `interactive_background` + zonas → página interactiva renderiza zonas clicleables.
2. Zona clic → product detail con `?color=pc_id` correcto.
3. Colección sin `interactive_background` → 404/redirect (forzar interactiva).
4. Editor: dibujar, mover, redimensionar, eliminar, guardar.
5. Validación: coordenadas fuera de [0,100] rechazadas.
6. Responsive: zonas mantienen proporción en pantallas grandes/pequeñas.

---

## Notas

- No se requieren librerías externas. El editor usa divs overlay + vanilla JS (~870 líneas).
- `product_color.product` debe ser accesible para construir el link del product detail.
- El display público no necesita JS: si JS falla, los `<a>` absolutos siguen funcionando.
- Comentarios en el código en inglés; strings de UI en español.

---

## Estado de ejecución

- ✅ Fase 1: modelo `InteractiveZone` + `interactive_background` + migración `0004`
- ✅ Fase 2: `CollectionDetailView` renderiza `collection_interactive.html` (404 si no hay fondo interactivo)
- ✅ Fase 3: editor visual de zonas (divs overlay) + API JSON (crear/listar/actualizar/eliminar)
- ✅ Fase 4: `interactive_background` en forms create/update, inline en admin, botón "Zonas" en listado
- ✅ Tests: 19 tests en `apps/products/tests/test_interactive_zones.py` + suite completa verde
- ✅ Limpieza: eliminado el sistema de theming legacy (colores, fuentes, efectos, custom_css, style_config) del modelo, views, forms, admin, templates, JS y constantes
