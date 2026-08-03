from django.contrib import admin
from django.utils.html import format_html
from .models import Gallery, HeroConfig, HomePromo
from .forms import HeroConfigCreateForm, HeroConfigUpdateForm, HeroConfigDeleteForm


@admin.register(HeroConfig)
class HeroConfigAdmin(admin.ModelAdmin):
    form = HeroConfigUpdateForm
    add_form = HeroConfigCreateForm
    list_display = ('title_preview', 'sort_order', 'is_active', 'background_preview', 'updated_at')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title_text', 'subtitle_text')
    
    fieldsets = (
        ('Configuración del Slide', {
            'fields': ('is_active', 'sort_order', 'background_image', 'overlay_opacity'),
            'classes': ('wide',)
        }),
        ('Contenido', {
            'fields': ('title_text', 'subtitle_text', 'button_text', 'button_url', 'button_style', 'content_alignment', 'section_height'),
            'classes': ('wide',)
        }),
        ('Estilos del Título', {
            'fields': ('title_font_family', 'title_font_size', 'title_font_weight', 'title_line_height', 'title_color', 'title_margin_bottom'),
            'classes': ('collapse',)
        }),
        ('Estilos del Subtítulo', {
            'fields': ('subtitle_font_family', 'subtitle_font_size', 'subtitle_font_weight', 'subtitle_line_height', 'subtitle_color', 'subtitle_margin_bottom'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs['form'] = self.add_form
        else:
            kwargs['form'] = self.form
        return super().get_form(request, obj, **kwargs)
    
    @admin.display(description='Slide')
    def title_preview(self, obj):
        return format_html(
            '<div style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">'
            '<strong>{}</strong><br><span style="color: #666;">{}</span></div>',
            obj.title_text[:30],
            obj.subtitle_text[:40] if obj.subtitle_text else ''
        )
    
    @admin.display(description='Fondo')
    def background_preview(self, obj):
        if obj.background_image and obj.background_image.url:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.background_image.url
            )
        return '-'
    
    class Media:
        css = {
            'all': ('css/admin/hero_admin.css',)
        }
        js = ('js/admin/hero_admin.js',)


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('description_preview', 'image_preview', 'sort_order', 'is_active', 'updated_at')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('description', 'alt_text')
    fields = ('is_active', 'sort_order', 'image', 'description', 'alt_text')

    @admin.display(description='Descripción')
    def description_preview(self, obj):
        return format_html('<strong>{}</strong>', obj.description[:60])

    @admin.display(description='Foto')
    def image_preview(self, obj):
        if obj.image and obj.image.url:
            return format_html(
                '<img src="{}" style="width: 40px; height: 60px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return '-'


@admin.register(HomePromo)
class HomePromoAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview', 'sort_order', 'is_active', 'updated_at')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')
    fields = ('is_active', 'sort_order', 'image', 'title', 'subtitle', 'link_url', 'link_text')

    @admin.display(description='Imagen')
    def image_preview(self, obj):
        if obj.image and obj.image.url:
            return format_html(
                '<img src="{}" style="width: 80px; height: 40px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return '-'