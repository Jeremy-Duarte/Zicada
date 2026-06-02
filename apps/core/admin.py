from django.contrib import admin
from .models import HeroConfig

class HeroConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Configuración del Slide', {
            'fields': ('is_active', 'order')
        }),
        ('Fondo', {
            'fields': ('background_image', 'overlay_opacity')
        }),
        ('Título', {
            'fields': ('title_text', 'title_font_family', 'title_font_size', 
                       'title_font_weight', 'title_line_height', 'title_color', 
                       'title_margin_bottom')
        }),
        ('Lema', {
            'fields': ('subtitle_text', 'subtitle_font_family', 'subtitle_font_size',
                       'subtitle_font_weight', 'subtitle_line_height', 'subtitle_color',
                       'subtitle_margin_bottom')
        }),
        ('Botón', {
            'fields': ('button_text', 'button_url', 'button_style')
        }),
        ('Diseño', {
            'fields': ('content_alignment', 'section_height')
        }),
    )
    
    list_display = ('title_text', 'order', 'is_active', 'updated_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)

admin.site.register(HeroConfig, HeroConfigAdmin)