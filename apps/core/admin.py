from django.contrib import admin
from django.utils.html import format_html
from .models import HeroConfig
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
            'fields': ('is_active', 'order', 'background_image', 'overlay_opacity'),
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
    
    def title_preview(self, obj):
        return format_html(
            '<div style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">'
            '<strong>{}</strong><br><span style="color: #666;">{}</span></div>',
            obj.title_text[:30],
            obj.subtitle_text[:40] if obj.subtitle_text else ''
        )
    title_preview.short_description = 'Slide'
    
    def background_preview(self, obj):
        if obj.background_image and obj.background_image.url:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.background_image.url
            )
        return '-'
    background_preview.short_description = 'Fondo'
    
    class Media:
        css = {
            'all': ('css/admin/hero_admin.css',)
        }
        js = ('js/admin/hero_admin.js',)