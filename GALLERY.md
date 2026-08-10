# Plan: Galería de Fotos Interactiva — Zicada

## 1. Objetivo
Construir un nuevo apartado "Galería" en el landing page de Zicada que muestre fotos configurables desde el backoffice, con layouts dinámicos (1×1, 2×2, 3×3, 4×4), redirección por foto, organización automática por relación de aspecto, entrega optimizada mediante el CDN de Cloudinary y una experiencia visual atractiva e interactiva usando Tailwind CSS.

## 2. Alcance
- Nuevo acceso de navegación "GALERÍA" en el header (desktop y móvil).
- Sección de galería en el home que puede llevar a una página dedicada `/galeria/`.
- Modelo de datos extensible con submodelo de configuración de layouts.
- Detección automática de relación de aspecto de cada foto para decidir su zona/visualización.
- CRUD completo en el backoffice bajo Configuración > Galería.
- Integración con Cloudinary para pre-render de thumbnails y lazy loading.
- Código mantenible, funciones pequeñas, identificadores semánticos en formularios y cumplimiento de estándares SonarQube.

## 3. Modelo de datos

### 3.1 `GalleryLayout` — submodelo de configuración
Ubicación: `apps/core/models.py`

Campos:
- `name`: `CharField(max_length=100)` — nombre descriptivo del layout (ej. "Grid 3×3").
- `columns`: `PositiveSmallIntegerField` — número de columnas (1, 2, 3, 4).
- `rows`: `PositiveSmallIntegerField` — número de filas (1, 2, 3, 4).
- `css_class`: `CharField(max_length=100)` — clase CSS utilitaria para el contenedor (ej. `grid-cols-1`, `grid-cols-2`, etc.).
- `max_photos`: `PositiveSmallIntegerField` — cantidad máxima de fotos que caben en el layout (calculado `columns * rows`).
- `sort_order`: `PositiveIntegerField(default=0)` — orden de presentación.
- `is_active`: `BooleanField(default=True)`.
- Hereda de `BaseAuditModel` para auditoría y soft-delete.

Métodos:
- `capacity() -> int`: retorna `columns * rows`.
- `__str__() -> str`: retorna el nombre del layout.

### 3.2 `GalleryPhoto` — fotografía de la galería
Ubicación: `apps/core/models.py`

Campos:
- `image`: `ImageField(upload_to='landingpage/gallery/photos/')` — archivo de la foto.
- `redirect_url`: `URLField(blank=True)` — destino al hacer clic.
- `title`: `CharField(max_length=200, blank=True)` — título/leyenda.
- `alt_text`: `CharField(max_length=255)` — texto alternativo (SEO/accesibilidad).
- `layout`: `ForeignKey(GalleryLayout, null=True, blank=True, on_delete=SET_NULL)` — layout explícito opcional.
- `aspect_ratio`: `FloatField(null=True, blank=True)` — relación de aspecto detectada (ancho / alto).
- `aspect_category`: `CharField(choices=...)` — categoría derivada: `square`, `portrait`, `landscape`, `wide`.
- `display_zone`: `CharField(max_length=50, blank=True)` — zona visual calculada automáticamente.
- `sort_order`: `PositiveIntegerField(default=0)`.
- `is_active`: `BooleanField(default=True)`.
- Hereda de `BaseAuditModel`.

Métodos:
- `compute_aspect_ratio() -> float | None`: lee las dimensiones de `image` y calcula ancho/alto.
- `compute_aspect_category() -> str`: categoriza según el aspect ratio.
- `compute_display_zone() -> str`: retorna el span de columnas según la categoría (`col-span-1` para vertical/cuadrada, `col-span-2` para horizontal/panorámica).
- `native_aspect_ratio_css -> str`: relación de aspecto nativa lista para la propiedad CSS `aspect-ratio`.
- `get_cloudinary_url(width: int, **transforms) -> str`: genera URL transformada por Cloudinary.
- `save()`: calcula aspecto y zona antes de guardar.

### 3.3 Decisiones de organización automática
- Se detecta la relación de aspecto real de la imagen al guardar y se respeta **primero el formato nativo** (fotos de teléfono vertical y horizontal).
- Se asigna una `aspect_category` automática:
  - `square`: 0.95 ≤ ratio ≤ 1.15
  - `portrait`: ratio < 0.95 (foto de teléfono vertical)
  - `landscape`: 1.15 < ratio ≤ 2.0 (foto de teléfono horizontal)
  - `wide`: ratio > 2.0
- La `display_zone` define el ancho (`col-span-1` o `col-span-2`); la **altura la fija el aspecto nativo** vía `aspect-ratio` en CSS, sin filas fijas ni recortes forzados.
- Las fotos horizontales (típicamente asignadas a layouts 1×1) ocupan más ancho; las verticales mantienen su proporción alta.
- El usuario puede sobrescribir el layout general asignando un `GalleryLayout` a la foto; el número de columnas del grid proviene del layout configurado.

## 4. Integración Cloudinary

### 4.1 Utilidad `apps/core/cloudinary_utils.py`
Funciones pequeñas y reutilizables:
- `build_cloudinary_url(image_field, width: int | None = None, height: int | None = None, crop: str = 'limit', quality: str = 'auto', fetch_format: str = 'auto') -> str`
- `get_thumbnail_url(image_field, width: int = 400) -> str`
- `get_hero_url(image_field, width: int = 1200) -> str`
- `parse_cloudinary_public_id(image_field) -> str | None`: extrae el public_id si la imagen está en Cloudinary.

### 4.2 Template tags
Ubicación: `apps/core/templatetags/gallery_tags.py`
- `{% cloudinary_url photo.image width=600 %}`
- `{% cloudinary_srcset photo.image sizes=[400,800,1200] %}`
- `{% gallery_photo_classes photo %}` — retorna las clases CSS de span según `display_zone`.

Se usa `f_auto,q_auto,w_<size>,c_limit` para pre-render optimizado y adaptación de formato WebP/AVIF cuando el navegador lo soporte.

## 5. Backend

### 5.1 Formularios — `apps/core/forms.py`
- `GalleryPhotoForm(FormStyleMixin, SortableCreateMixin | SortableUpdateMixin, ModelForm)`
  - Campos: `image`, `redirect_url`, `title`, `alt_text`, `layout`, `sort_order`, `is_active`.
  - Widget `image`: `CloudinarySingleImageWidget`.
  - `clean_redirect_url()`: valida URL interna o externa segura.
  - `clean_image()`: valida tamaño máximo 5 MB y dimensiones mínimas.
  - `save()`: invoca `compute_aspect_ratio`, `compute_aspect_category`, `compute_display_zone`.
- `GalleryLayoutForm(ModelForm)`
  - Campos: `name`, `columns`, `rows`, `css_class`, `max_photos`, `sort_order`, `is_active`.
  - `clean()`: valida que `max_photos` coincida con `columns * rows`.

### 5.2 Vistas — `apps/core/views.py`
Clases basadas en vistas con `StaffPermissionRequiredMixin`:
- `GalleryPhotoListView`
- `GalleryPhotoCreateView`
- `GalleryPhotoUpdateView`
- `GalleryPhotoDeleteView` (soft-delete)
- `GalleryPhotoRestoreView`
- `GalleryPhotoTrashcanView`
- `GalleryLayoutListView`, `GalleryLayoutCreateView`, `GalleryLayoutUpdateView`, `GalleryLayoutDeleteView`

Vista pública:
- `gallery_page(request)`: lista fotos activas con layouts, prepara datos para el template.

### 5.3 URLs — `apps/core/urls.py`
- `/galeria/` → `gallery_page`
- `/admin/galeria/fotos/` → listado
- `/admin/galeria/fotos/crear/` → crear
- `/admin/galeria/fotos/<int:pk>/editar/` → editar
- `/admin/galeria/fotos/<int:pk>/eliminar/` → eliminar
- `/admin/galeria/fotos/<int:pk>/restaurar/` → restaurar
- `/admin/galeria/fotos/papelera/` → papelera
- `/admin/galeria/layouts/` → layouts
- `/admin/galeria/layouts/crear/`, `/admin/galeria/layouts/<int:pk>/editar/`, etc.

### 5.4 Backoffice dashboard
En `apps/backoffice/views.py` `AdminConfigView`, añadir botones de acceso rápido:
- "Galería de Fotos" → listado de fotos.
- "Layouts de Galería" → listado de layouts.
- "Papelera de Galería" → fotos eliminadas.

## 6. Frontend

### 6.1 Header — `apps/core/templates/components/header.html`
Añadir enlace "GALERÍA" junto a "COLECCIONES" en desktop y móvil, apuntando a `{% url 'core:gallery' %}`.

### 6.2 Página de galería — `apps/core/templates/core/gallery_page.html`
- Extiende `layouts/base.html`.
- Encabezado atractivo con título "Galería Zicada".
- Grid/masonry dinámico usando las clases CSS generadas por `display_zone`.
- Cada foto es un enlace si tiene `redirect_url`.
- Efectos hover: escala sutil, overlay con título, sombra.
- Lazy loading nativo (`loading="lazy"`) y `srcset` con Cloudinary.
- Modal/lightbox con Alpine.js para vista ampliada sin salir de la página.
- Botón "Ver más" o scroll infinito opcional si hay muchas fotos.

### 6.3 Sección en landing page — `apps/core/templates/home.html`
Añadir una sección "Galería destacada" que muestre las primeras 6–8 fotos activas con un botón "Ver galería completa".

### 6.4 Estilos
- Únicamente Tailwind CSS; sin CSS personalizado.
- Clases de grid: `grid`, `grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`, `gap-4`, `auto-rows-[200px]`.
- Variantes de span generadas por el modelo:
  - `square`: `col-span-1 row-span-1`
  - `portrait`: `col-span-1 row-span-2`
  - `landscape`: `col-span-2 row-span-1`
  - `wide`: `col-span-2 row-span-2` o `col-span-3 row-span-1` según layout.
- Animaciones: `transition-transform duration-300 hover:scale-105`, `group-hover:opacity-100`.

### 6.5 Scripts
- `static/js/core/gallery-lightbox.js`: controla el modal/lightbox con Alpine.js o vanilla JS pequeño.
- `static/js/core/gallery-lazy.js`: lazy loading progresivo opcional.

## 7. Tests
Ubicación: `apps/core/tests/`

- `test_gallery_models.py`
  - Creación de `GalleryLayout` y `GalleryPhoto`.
  - Cálculo correcto de aspect ratio y categoría.
  - Soft-delete y restauración.
- `test_gallery_views.py`
  - Acceso público a `/galeria/`.
  - CRUD con permisos de administrador.
  - Validaciones de formulario.
- `test_cloudinary_utils.py`
  - Mock de imágenes para probar URLs de Cloudinary sin subir archivos reales.

Se usa `config.settings_test` y se mockean las imágenes (no se toca Cloudinary real).

## 8. Migraciones
- Generar migración `0007_gallerylayout_galleryphoto.py` (o siguiente disponible) con `python manage.py makemigrations`.
- Aplicar con `python manage.py migrate`.

## 9. Estándares de calidad
- Funciones menores a 15 líneas; extraer helpers a `apps/core/utils.py` o `apps/core/cloudinary_utils.py`.
- Type hints en firmas de funciones.
- Nombres en inglés para modelos, vistas y funciones; español solo en strings de UI.
- Uso de `select_related`/`prefetch_related` en querysets.
- Validaciones en formularios, no en vistas.
- Identificadores semánticos en formularios (`id_gallery_photo_image`, etc.).
- No duplicar código; reutilizar `FormStyleMixin`, `SortableCreateMixin`, `SortableUpdateMixin`, `StaffPermissionRequiredMixin`.
- Evitar advertencias de SonarQube: sin variables muertas, sin concatenación insegura, sin funciones excesivamente complejas.

## 10. Comandos de verificación
```bash
python manage.py makemigrations --check
python manage.py migrate
DJANGO_SETTINGS_MODULE=config.settings_test pytest apps/core/tests/test_gallery_models.py apps/core/tests/test_gallery_views.py apps/core/tests/test_cloudinary_utils.py -v
DJANGO_SETTINGS_MODULE=config.settings_test pytest apps/core/ -v
```

## 11. Notas de implementación
- No modificar el modelo `Gallery` existente (carrusel TikTok); el nuevo apartado usa `GalleryPhoto`.
- El layout por defecto será 3×3 si no se configura ninguno.
- Las fotos sin `redirect_url` se abrirán en el lightbox; las que tengan `redirect_url` navegarán al enlace (con `target="_blank"` si es externo).
- Se respetará `prefers-reduced-motion` para animaciones.
