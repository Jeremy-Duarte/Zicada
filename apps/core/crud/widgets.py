import json
from django import forms
from django.forms import widgets
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.core.cache import cache
from apps.products.models import ProductImage


class CloudinaryImageSelectWidget(widgets.SelectMultiple):
    """Widget para seleccionar múltiples imágenes para un ProductColor."""

    def __init__(self, product_color_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_color_id = product_color_id

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs, {'name': name, 'class': 'hidden'})
        if value is None:
            value = []
        if not isinstance(value, (list, tuple)):
            value = [value]

        # MOSTRAR TODAS LAS IMÁGENES, sin filtrar por product_color_id
        # Solo se usa product_color_id para saber cuáles están seleccionadas
        images = ProductImage.objects.all().order_by('-created_at')

        selected_ids = [str(v) for v in value]

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
        # Mostrar TODAS las imágenes en el select oculto
        cache_key = 'product_images_all'
        all_images = cache.get(cache_key)
        if all_images is None:
            all_images = list(ProductImage.objects.only('pk', 'image').order_by('-created_at'))
            cache.set(cache_key, all_images, 60 * 5)

        selected_set = set(selected_values)
        options = [
            f'<option value="{img.pk}"{" selected" if str(img.pk) in selected_set else ""}>{img.image.url}</option>'
            for img in all_images
        ]

        select_attrs = ' '.join([f'{k}="{escape(str(v))}"' for k, v in attrs.items()])
        return f'<select {select_attrs} multiple>{"".join(options)}</select>'

    def _render_image_grid(self, images, selected_ids, name):
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
                <label class="relative cursor-pointer group" data-image-id="{img.pk}">
                    <input type="checkbox" name="{name}" value="{img.pk}" {checked_attr}
                        data-src="{img.image.url}" data-alt="{escape(img.alt_text or 'Imagen')}"
                        class="absolute opacity-0 w-0 h-0 peer">
                    <div class="relative rounded-lg overflow-hidden border-2 transition-all 
                                {'border-zicada-accent ring-2 ring-zicada-accent/50' if is_selected else 'border-gray-200'}
                                group-hover:border-zicada-accent group-hover:shadow-md">
                        <img src="{img.image.url}" alt="{escape(img.alt_text or 'Imagen')}"
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
    """Widget para seleccionar imagen destacada de un ProductColor."""

    def __init__(self, product_color_id=None, images_widget_name='images', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_color_id = product_color_id
        self.images_widget_name = images_widget_name

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs, {'name': name, 'class': 'hidden'})
        select_html = self._render_hidden_select(name, value, final_attrs)

        return mark_safe(f'''
            <div class="cloudinary-featured-widget" 
                 data-widget-name="{name}"
                 data-images-widget-name="{self.images_widget_name}"
                 data-product-color-id="{self.product_color_id or ''}"
                 data-initial-value="{escape(str(value or ''))}">
                {select_html}
                <div class="featured-images-grid grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 mt-3">
                    <div class="col-span-full text-center py-8 text-gray-400">
                        <i class="fas fa-spinner fa-spin text-2xl mb-2 block"></i>
                        <p>Cargando imágenes disponibles...</p>
                    </div>
                </div>
                <p class="text-xs text-gray-400 mt-2 flex items-center gap-1">
                    <i class="fas fa-info-circle"></i>
                    Selecciona la imagen destacada para este color.
                </p>
            </div>
        ''')

    def _render_hidden_select(self, name, value, attrs):
        # Mostrar TODAS las imágenes
        cache_key = 'product_images_all'
        all_images = cache.get(cache_key)
        if all_images is None:
            all_images = list(ProductImage.objects.only('pk', 'image').order_by('-created_at'))
            cache.set(cache_key, all_images, 60 * 5)

        selected_set = {str(value)} if value else set()
        options = ['<option value="">---------</option>']
        options += [
            f'<option value="{img.pk}"{" selected" if str(img.pk) in selected_set else ""}>{img.pk}</option>'
            for img in all_images
        ]
        select_attrs = ' '.join([f'{k}="{escape(str(v))}"' for k, v in attrs.items()])
        return f'<select {select_attrs}>{"".join(options)}</select>'

    class Media:
        js = ('js/core/cloudinary-featured-widget.js',)

class CloudinarySingleImageWidget(forms.ClearableFileInput):
    """Widget para seleccionar una sola imagen con vista previa."""

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        
        preview_html = ''
        if value and hasattr(value, 'url'):
            preview_html = f'''
                <div class="mt-3 relative inline-block">
                    <img src="{value.url}" class="w-32 h-32 object-cover rounded-lg shadow-md border-2 border-green-500">
                    <span class="absolute -top-2 -right-2 bg-green-500 text-white text-xs rounded-full px-1.5 py-0.5">
                        <i class="fas fa-check"></i>
                    </span>
                    <p class="text-xs text-gray-500 mt-2">Imagen actual</p>
                </div>
            '''
        else:
            preview_html = '''
                <div class="mt-3 text-center text-gray-400">
                    <i class="fas fa-image text-3xl mb-1 block"></i>
                    <p class="text-xs">Sin imagen seleccionada</p>
                </div>
            '''
        
        return mark_safe(f'''
            <div class="cloudinary-single-image-widget">
                <div class="flex flex-col">
                    {input_html}
                    <div class="single-image-preview">
                        {preview_html}
                    </div>
                    <p class="text-xs text-gray-400 mt-2">
                        <i class="fas fa-info-circle"></i> Sube una imagen (recomendado: 1920x1080px)
                    </p>
                </div>
            </div>
        ''')

    class Media:
        js = ('js/widgets/cloudinary-single-image.js',)


class SortableOrderWidget(forms.Widget):
    """Widget para ordenar ProductColors o ProductVariants."""

    def __init__(self, queryset=None, item_label=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = queryset
        self.item_label = item_label

    def render(self, name, value, attrs=None, renderer=None):
        if self.queryset is None:
            return '<p class="text-red-500">Error: No se proporcionaron elementos para ordenar</p>'

        ids = [str(item.pk) for item in self.queryset]

        final_attrs = self.build_attrs(attrs, {
            'name': name,
            'type': 'hidden',
            'class': 'sortable-order-input',
            'value': json.dumps(ids)
        })
        attrs_str = ' '.join(f'{k}="{escape(str(v))}"' for k, v in final_attrs.items())
        input_html = f'<input {attrs_str}>'
        sortable_html = self._render_sortable_list()

        return mark_safe(f'''
            <div class="sortable-order-widget">
                <label class="block text-sm font-medium text-gray-700 mb-2">Orden</label>
                {input_html}
                {sortable_html}
                <p class="text-xs text-gray-400 mt-2">Arrastra para reordenar</p>
            </div>
        ''')

    def _render_sortable_list(self):
        items_html = []
        for idx, item in enumerate(self.queryset):
            label = self._get_item_label(item)
            items_html.append(f'''
                <li data-id="{item.pk}" data-order="{idx}"
                    class="sortable-item flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-move">
                    <div class="flex items-center gap-3">
                        <i class="fas fa-grip-vertical"></i>
                        <span>{escape(str(label))}</span>
                    </div>
                    <span class="text-xs">Orden: {idx}</span>
                </li>
            ''')
        return f'<ul class="sortable-list space-y-2">{"".join(items_html)}</ul>'

    def _get_item_label(self, item):
        if callable(self.item_label):
            return self.item_label(item)
        if isinstance(self.item_label, str):
            return getattr(item, self.item_label, str(item))
        return str(item)

    class Media:
        js = ('js/core/sortable-widget.js',)


class DeliveryUserRadioWidget(forms.RadioSelect):
    """Widget para seleccionar repartidor con tarjetas visuales."""

    def render(self, name, value, attrs=None, renderer=None):
        if not self.choices:
            return '<p class="text-gray-500 text-center py-4">No hay repartidores disponibles</p>'

        output = ['<div class="space-y-2" id="delivery-list">']

        for choice_value, choice_label in self.choices:
            checked = 'checked' if str(choice_value) == str(value) else ''

            if hasattr(choice_label, 'get_full_name'):
                full_name = choice_label.get_full_name() or choice_label.username
                phone = getattr(choice_label, 'phone', '')
            else:
                full_name = str(choice_label)
                phone = ''

            search_text = f"{full_name} {phone}".lower()

            output.append(f'''
                <label class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition
                            {'border-zicada-accent bg-zicada-accent/5' if checked else 'border-gray-200'}"
                        data-search="{escape(search_text)}">
                    <input type="radio" name="{name}" value="{choice_value}" {checked} class="w-4 h-4 text-zicada-accent">
                    <div class="flex-1">
                        <div class="font-medium text-gray-800">{escape(full_name)}</div>
                        {f'<div class="text-sm text-gray-500">📞 {escape(phone)}</div>' if phone else ''}
                    </div>
                </label>
            ''')

        output.append('</div>')
        return mark_safe(''.join(output))