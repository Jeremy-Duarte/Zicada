from django import forms
from django.forms import widgets
from django.urls import reverse
from django.utils.safestring import mark_safe
from apps.products.models import ProductImage


class CloudinaryImageSelectWidget(widgets.SelectMultiple):
    """
    Widget para seleccionar múltiples imágenes de Cloudinary con vista previa en grid.
    Reemplaza el select múltiple aburrido por una cuadrícula de miniaturas.
    """

    template_name = 'widgets/cloudinary_image_select.html'

    def render(self, name, value, attrs=None, renderer=None):
        # Construir el select oculto
        final_attrs = self.build_attrs(attrs, {'name': name, 'class': 'hidden'})
        if value is None:
            value = []
        if not isinstance(value, (list, tuple)):
            value = [value]

        # Obtener todas las imágenes activas
        images = ProductImage.objects.all().order_by('-created_at')
        selected_ids = [str(v) for v in value]

        # Construir HTML del grid
        grid_html = self._render_image_grid(images, selected_ids, name)
        select_html = self._render_hidden_select(name, selected_ids, final_attrs)

        return mark_safe(f"""
            <div class="cloudinary-image-widget" data-widget-name="{name}">
                {select_html}
                <div class="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 mt-3">
                    {grid_html}
                </div>
            </div>
        """)

    def _render_hidden_select(self, name, selected_values, attrs):
        """Genera el select oculto que mantiene los valores seleccionados."""
        options = []
        # Necesitamos todas las opciones posibles para que el formulario pueda enviar los valores
        # Pero como estamos usando checkboxes, el select debe tener todas las imágenes como opciones.
        all_images = ProductImage.objects.all()
        for img in all_images:
            selected_attr = ' selected' if str(img.pk) in selected_values else ''
            options.append(f'<option value="{img.pk}"{selected_attr}>{img.image.url}</option>')
        select_attrs = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
        return f'<select {select_attrs} multiple>{"" .join(options)}</select>'

    def _render_image_grid(self, images, selected_ids, name):
        """Genera el grid de imágenes con checkboxes."""
        if not images.exists():
            upload_url = reverse('products:productimage_create')
            return f'''
                <div class="col-span-full text-center py-8 text-gray-400">
                    <i class="fas fa-images text-3xl mb-2 block"></i>
                    <p>No hay imágenes disponibles.</p>
                    <a href="{upload_url}" target="_blank" class="text-zicada-accent hover:underline inline-block mt-2">
                        Subir imagen
                    </a>
                </div>
            '''

        grid_items = []
        for img in images:
            is_selected = str(img.pk) in selected_ids
            checked_attr = 'checked' if is_selected else ''
            grid_items.append(f'''
                <label class="relative cursor-pointer group">
                    <input type="checkbox" name="{name}" value="{img.pk}" {checked_attr}
                           class="absolute opacity-0 w-0 h-0 peer">
                    <div class="relative rounded-lg overflow-hidden border-2 transition-all 
                                {'border-zicada-accent ring-2 ring-zicada-accent/50' if is_selected else 'border-gray-200'}
                                group-hover:border-zicada-accent group-hover:shadow-md">
                        <img src="{img.image.url}" alt="{img.alt_text or 'Imagen'}"
                             class="w-full h-24 object-cover">
                        <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 peer-checked:opacity-100 transition-opacity">
                            <i class="fas fa-check-circle text-white text-2xl drop-shadow-md"></i>
                        </div>
                    </div>
                    <div class="absolute top-1 right-1 w-5 h-5 rounded-full bg-white shadow-sm flex items-center justify-center">
                        <div class="w-4 h-4 rounded-full transition-colors 
                                    {'bg-zicada-accent' if is_selected else 'bg-gray-300'} peer-checked:bg-zicada-accent">
                        </div>
                    </div>
                </label>
            ''')

        # Opcional: botón para subir nueva imagen
        upload_url = reverse('products:productimage_create')
        grid_items.append(f'''
            <a href="{upload_url}" target="_blank"
               class="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg h-24
                      hover:border-zicada-accent transition group">
                <i class="fas fa-plus text-gray-400 text-xl group-hover:text-zicada-accent"></i>
                <span class="text-xs text-gray-400 mt-1">Subir</span>
            </a>
        ''')

        return ''.join(grid_items)

    class Media:
        js = ('js/core/cloudinary-widget.js',)

class CloudinaryFeaturedImageWidget(widgets.Select):
    """
    Widget para seleccionar imagen destacada.
    Muestra SOLO las imágenes seleccionidas en el widget 'images'.
    Selección única, con radio buttons.
    """

    def __init__(self, images_widget_name='images', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.images_widget_name = images_widget_name

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs, {'name': name, 'class': 'hidden'})
        
        select_html = self._render_hidden_select(name, value, final_attrs)
        
        return mark_safe(f'''
            <div class="cloudinary-featured-widget" 
                 data-widget-name="{name}"
                 data-images-widget-name="{self.images_widget_name}"
                 data-initial-value="{value or ''}">
                {select_html}
                <div class="featured-images-grid grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 mt-3">
                    <div class="col-span-full text-center py-8 text-gray-400">
                        <i class="fas fa-spinner fa-spin text-2xl mb-2 block"></i>
                        <p>Cargando imágenes seleccionadas...</p>
                    </div>
                </div>
                <p class="text-xs text-gray-400 mt-2 flex items-center gap-1">
                    <i class="fas fa-info-circle"></i>
                    Solo se muestran las imágenes seleccionadas arriba. Selecciona una como destacada.
                </p>
            </div>
        ''')
    
    def _render_hidden_select(self, name, value, attrs):
        options = ['<option value="">---------</option>']
        # Si hay un valor inicial, creamos una opción seleccionada
        if value:
            options.append(f'<option value="{value}" selected>{value}</option>')
        
        select_attrs = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
        return f'<select {select_attrs} multiple>{"" .join(options)}</select>'
    
    class Media:
        js = ('js/core/cloudinary-featured-widget.js',)