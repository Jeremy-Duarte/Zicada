"""
Constantes centralizadas para opciones de diseño reutilizables en toda la aplicación.
Estas opciones se usan en formularios de Hero, Colecciones, Productos, etc.
"""

from django.utils.translation import gettext_lazy as _

# =============================================================================
# TIPOGRAFÍA
# =============================================================================

FONT_FAMILY_CHOICES = [
    ("'Inter', sans-serif", "🔤 Inter (Moderno)"),
    ("'Roboto', sans-serif", "🔤 Roboto (Versátil)"),
    ("'Poppins', sans-serif", "🔤 Poppins (Geométrico)"),
    ("'Montserrat', sans-serif", "🔤 Montserrat (Elegante)"),
    ("'Open Sans', sans-serif", "🔤 Open Sans (Legible)"),
    ("'Playfair Display', serif", "✒️ Playfair Display (Clásico)"),
    ("'Merriweather', serif", "✒️ Merriweather (Serif)"),
    ("'Oswald', sans-serif", "🔤 Oswald (Impactante)"),
    ("'Raleway', sans-serif", "🔤 Raleway (Delicado)"),
    ("'Lato', sans-serif", "🔤 Lato (Amigable)"),
]

FONT_WEIGHT_CHOICES = [
    ('300', 'Light (300) - Delgada'),
    ('400', 'Regular (400) - Normal'),
    ('500', 'Medium (500) - Mediana'),
    ('600', 'Semi Bold (600) - Seminegrita'),
    ('700', 'Bold (700) - Negrita'),
    ('800', 'Extra Bold (800) - Extranegrita'),
    ('900', 'Black (900) - Negra'),
]

FONT_SIZE_CHOICES = [
    ('0.75rem', 'XS - Extra pequeño (0.75rem)'),
    ('0.875rem', 'SM - Pequeño (0.875rem)'),
    ('1rem', 'Base - Normal (1rem)'),
    ('1.125rem', 'LG - Ligeramente grande (1.125rem)'),
    ('1.25rem', 'XL - Grande (1.25rem)'),
    ('1.5rem', '2XL - Muy grande (1.5rem)'),
    ('1.875rem', '3XL - Extra grande (1.875rem)'),
    ('2.25rem', '4XL - Gigante (2.25rem)'),
    ('3rem', '5XL - Muy gigante (3rem)'),
    ('3.75rem', '6XL - Masivo (3.75rem)'),
    ('4.5rem', '7XL - Épico (4.5rem)'),
    ('6rem', '8XL - Colosal (6rem)'),
]

LINE_HEIGHT_CHOICES = [
    ('1', 'Compacto (1) - Sin espacio'),
    ('1.2', 'Apretado (1.2) - Poco espacio'),
    ('1.4', 'Normal (1.4) - Estándar'),
    ('1.6', 'Espaciado (1.6) - Cómodo'),
    ('1.8', 'Muy espaciado (1.8) - Aireado'),
    ('2', 'Doble (2) - Mucho espacio'),
]

MARGIN_CHOICES = [
    ('0', 'Ninguno (0)'),
    ('0.25rem', 'Muy pequeño (0.25rem)'),
    ('0.5rem', 'Pequeño (0.5rem)'),
    ('0.75rem', 'Mediano-pequeño (0.75rem)'),
    ('1rem', 'Normal (1rem)'),
    ('1.25rem', 'Mediano (1.25rem)'),
    ('1.5rem', 'Grande (1.5rem)'),
    ('2rem', 'Muy grande (2rem)'),
    ('2.5rem', 'Extra grande (2.5rem)'),
    ('3rem', 'Gigante (3rem)'),
]

# =============================================================================
# COLORES
# =============================================================================

COLOR_PALETTES = {
    'zicada': {
        'primary': '#c2a575', 'secondary': '#8b5e3c',
        'background': '#ffffff', 'text': '#1a1a1a',
        'name': '🎨 Zicada (Oro)',
    },
    'elegant': {
        'primary': '#2d2d2d', 'secondary': '#1a1a1a',
        'background': '#fafafa', 'text': '#2d2d2d',
        'name': '🎨 Elegante (Negro)',
    },
    'vibrant': {
        'primary': '#e63946', 'secondary': '#c1121f',
        'background': '#ffffff', 'text': '#1d3557',
        'name': '🎨 Vibrante (Rojo)',
    },
    'ocean': {
        'primary': '#0077b6', 'secondary': '#00b4d8',
        'background': '#f0f8ff', 'text': '#03045e',
        'name': '🎨 Océano (Azul)',
    },
    'nature': {
        'primary': '#2d6a4f', 'secondary': '#40916c',
        'background': '#f4f1de', 'text': '#1b4332',
        'name': '🎨 Naturaleza (Verde)',
    },
    'luxury': {
        'primary': '#d4af37', 'secondary': '#9c7e2c',
        'background': '#1a1a1a', 'text': '#f5f5f5',
        'name': '🎨 Lujo (Dorado/Negro)',
    },
    'pastel': {
        'primary': '#f4a261', 'secondary': '#e76f51',
        'background': '#fdf6e3', 'text': '#2d3436',
        'name': '🎨 Pastel (Cálido)',
    },
    'minimal': {
        'primary': '#6c757d', 'secondary': '#495057',
        'background': '#ffffff', 'text': '#212529',
        'name': '🎨 Minimalista (Gris)',
    },
}

# Colores individuales (usando valores únicos, no duplicados de las paletas)
PRIMARY_COLORS = [
    ('#c2a575', 'Oro Zicada'),
    ('#2d2d2d', 'Negro elegante'),
    ('#e63946', 'Rojo vibrante'),
    ('#0077b6', 'Azul océano'),
    ('#2d6a4f', 'Verde naturaleza'),
    ('#d4af37', 'Dorado lujo'),
    ('#f4a261', 'Naranja cálido'),
    ('#6c757d', 'Gris minimalista'),
    ('#9b59b6', 'Púrpura'),
    ('#3498db', 'Azul cielo'),
]

SECONDARY_COLORS = [
    ('#8b5e3c', 'Marrón Zicada'),
    ('#1a1a1a', 'Negro'),
    ('#c1121f', 'Rojo intenso'),
    ('#00b4d8', 'Azul claro'),
    ('#40916c', 'Verde claro'),
    ('#9c7e2c', 'Dorado oscuro'),
    ('#e76f51', 'Terracota'),
    ('#495057', 'Gris oscuro'),
]

BACKGROUND_COLORS = [
    ('#ffffff', 'Blanco'),
    ('#fafafa', 'Gris muy claro'),
    ('#f0f8ff', 'Azul muy claro'),
    ('#f4f1de', 'Crema'),
    ('#1a1a1a', 'Negro'),
    ('#2d3436', 'Gris oscuro'),
    ('#fdf6e3', 'Beige'),
]

TEXT_COLORS = [
    ('#1a1a1a', 'Negro'),
    ('#2d2d2d', 'Gris oscuro'),
    ('#1d3557', 'Azul noche'),
    ('#03045e', 'Azul profundo'),
    ('#212529', 'Gris carbón'),
    ('#f5f5f5', 'Blanco (fondo oscuro)'),
    ('#e0e0e0', 'Gris claro (fondo oscuro)'),
]

# =============================================================================
# BOTONES - BASE (valores reutilizables)
# =============================================================================

BUTTON_BG_CHOICES = [
    ('bg-zicada-accent', '🔴 Rojo Zicada'),
    ('bg-black', '⚫ Negro'),
    ('bg-white', '⚪ Blanco'),
    ('bg-gray-800', '🌑 Gris oscuro'),
    ('bg-gray-100', '☁️ Gris claro'),
    ('bg-blue-600', '💙 Azul'),
    ('bg-green-600', '💚 Verde'),
    ('bg-purple-600', '💜 Morado'),
    ('bg-amber-600', '🟠 Ámbar'),
    ('bg-transparent', '✨ Transparente'),
]

BUTTON_HOVER_CHOICES = [
    ('hover:bg-red-700', '🔴 Rojo más oscuro'),
    ('hover:bg-gray-700', '⚫ Negro más oscuro'),
    ('hover:bg-gray-100', '⚪ Gris claro'),
    ('hover:bg-gray-900', '🌑 Negro intenso'),
    ('hover:bg-blue-700', '💙 Azul más oscuro'),
    ('hover:bg-green-700', '💚 Verde más oscuro'),
    ('hover:bg-purple-700', '💜 Morado más oscuro'),
    ('hover:bg-amber-700', '🟠 Ámbar más oscuro'),
    ('hover:bg-white', '⚪ Blanco'),
    ('hover:bg-opacity-90', '🎨 90% opacidad'),
    ('hover:scale-105', '📏 Escalar 5%'),
    ('hover:scale-110', '📏 Escalar 10%'),
]

BUTTON_TEXT_COLOR_CHOICES = [
    ('text-white', '⚪ Blanco'),
    ('text-gray-900', '⚫ Negro'),
    ('text-gray-700', '🌑 Gris oscuro'),
    ('text-gray-500', '🌫️ Gris medio'),
    ('text-zicada-accent', '🔴 Rojo Zicada'),
    ('text-blue-600', '💙 Azul'),
]

BUTTON_BORDER_RADIUS_CHOICES = [
    ('rounded-none', '🔲 Cuadrado'),
    ('rounded-sm', '📐 Ligeramente redondeado'),
    ('rounded-md', '📐 Medianamente redondeado'),
    ('rounded-lg', '🟨 Redondeado'),
    ('rounded-xl', '🟩 Muy redondeado'),
    ('rounded-2xl', '🟢 Extra redondeado'),
    ('rounded-full', '⚪ Círculo completo'),
]

BUTTON_SIZE_CHOICES = [
    ('px-2 py-1 text-xs', 'Extra pequeño'),
    ('px-3 py-1.5 text-sm', 'Pequeño'),
    ('px-4 py-2 text-base', 'Mediano'),
    ('px-6 py-2.5 text-base', 'Mediano-grande'),
    ('px-8 py-3 text-lg', 'Grande (recomendado)'),
    ('px-10 py-4 text-xl', 'Muy grande'),
    ('px-12 py-5 text-2xl', 'Extra grande'),
]

BUTTON_SHADOW_CHOICES = [
    ('shadow-none', 'Sin sombra'),
    ('shadow-sm', 'Sombra suave'),
    ('shadow', 'Sombra normal'),
    ('shadow-md', 'Sombra media'),
    ('shadow-lg', 'Sombra grande'),
    ('shadow-xl', 'Sombra extra grande'),
    ('shadow-2xl', 'Sombra masiva'),
]

BUTTON_WIDTH_CHOICES = [
    ('inline-block', 'Automático (según el texto)'),
    ('w-auto', 'Auto ajustable'),
    ('w-full', 'Ancho completo'),
    ('w-32', 'Fijo (128px)'),
    ('w-40', 'Fijo (160px)'),
    ('w-48', 'Fijo (192px)'),
    ('w-56', 'Fijo (224px)'),
    ('w-64', 'Fijo (256px)'),
]

# =============================================================================
# DISEÑO GENERAL
# =============================================================================

ALIGNMENT_CHOICES = [
    ('center', 'Centrado'),
    ('left', 'Izquierda'),
    ('right', 'Derecha'),
    ('justify', 'Justificado'),
]

SECTION_HEIGHT_CHOICES = [(f'{i}vh', f'{i}% de la pantalla') for i in range(10, 101, 10)]

# =============================================================================
# TARJETAS (usando valores existentes para evitar duplicación)
# =============================================================================

# Reutilizamos choices existentes para tarjetas
CARD_BORDER_RADIUS_CHOICES = BUTTON_BORDER_RADIUS_CHOICES
CARD_SHADOW_CHOICES = BUTTON_SHADOW_CHOICES

CARD_HOVER_SCALE_CHOICES = [
    ('1.00', 'Sin escala'),
    ('1.02', 'Muy sutil (2%)'),
    ('1.05', 'Sutil (5% - recomendado)'),
    ('1.08', 'Notable (8%)'),
    ('1.10', 'Fuerte (10%)'),
    ('1.15', 'Muy fuerte (15%)'),
]

# =============================================================================
# BADGES
# =============================================================================

STOCK_BADGE_COLORS = [
    ('bg-green-100 text-green-700', 'Disponible - Verde'),
    ('bg-orange-100 text-orange-700', 'Bajo stock - Naranja'),
    ('bg-red-100 text-red-700', 'Agotado - Rojo'),
    ('bg-blue-100 text-blue-700', 'Información - Azul'),
    ('bg-purple-100 text-purple-700', 'Especial - Púrpura'),
]

# =============================================================================
# VALORES POR DEFECTO
# =============================================================================

DEFAULT_PRIMARY_COLOR = '#c2a575'
DEFAULT_SECONDARY_COLOR = '#8b5e3c'
DEFAULT_BACKGROUND_COLOR = '#ffffff'
DEFAULT_TEXT_COLOR = '#1a1a1a'
DEFAULT_TITLE_FONT = "'Inter', sans-serif"
DEFAULT_BORDER_RADIUS = '0.5rem'
DEFAULT_BOX_SHADOW = '0 1px 3px 0 rgba(0,0,0,0.1)'
DEFAULT_HOVER_SCALE = 1.05
DEFAULT_SHOW_CATEGORY = True
DEFAULT_SHOW_STOCK_BADGE = True
DEFAULT_BADGE_TEXT_COLOR = '#ffffff'

# =============================================================================
# HELPERS
# =============================================================================

def get_color_palette_choices():
    """Retorna las opciones de paletas de colores para selects rápidos"""
    return [(key, palette['name']) for key, palette in COLOR_PALETTES.items()]

def apply_color_palette(instance, palette_key, save=False):
    """Aplica una paleta de colores predefinida a una instancia"""
    if palette_key in COLOR_PALETTES:
        palette = COLOR_PALETTES[palette_key]
        instance.primary_color = palette['primary']
        instance.secondary_color = palette['secondary']
        instance.background_color = palette['background']
        instance.text_color = palette['text']
        if save:
            instance.save()
        return True
    return False