"""
Constantes centralizadas para opciones de diseño reutilizables en toda la aplicación.
Estas opciones se usan en formularios de Hero, Colecciones, Productos, etc.
"""

from django.utils.translation import gettext_lazy as _

# =============================================================================
# ETIQUETAS DE UI
# =============================================================================

# Colores básicos
LABEL_RED = '🔴 Rojo Zicada'
LABEL_BLACK = '⚫ Negro'
LABEL_WHITE = '⚪ Blanco'
LABEL_DARK_GRAY = '🌑 Gris oscuro'
LABEL_LIGHT_GRAY = '☁️ Gris claro'
LABEL_BLUE = '💙 Azul'
LABEL_GREEN = '💚 Verde'
LABEL_PURPLE = '💜 Morado'
LABEL_AMBER = '🟠 Ámbar'
LABEL_TRANSPARENT = '✨ Transparente'

# Colores hover
LABEL_RED_DARKER = '🔴 Rojo más oscuro'
LABEL_BLACK_DARKER = '⚫ Negro más oscuro'
LABEL_BLUE_DARKER = '💙 Azul más oscuro'
LABEL_GREEN_DARKER = '💚 Verde más oscuro'
LABEL_PURPLE_DARKER = '💜 Morado más oscuro'
LABEL_AMBER_DARKER = '🟠 Ámbar más oscuro'
LABEL_DARK_INTENSE = '🌑 Negro intenso'

# Efectos hover
LABEL_OPACITY_90 = '🎨 90% opacidad'
LABEL_SCALE_5 = '📏 Escalar 5%'
LABEL_SCALE_10 = '📏 Escalar 10%'

# Bordes
LABEL_BORDER_NONE = '🔲 Cuadrado'
LABEL_BORDER_SM = '📐 Ligeramente redondeado'
LABEL_BORDER_MD = '📐 Medianamente redondeado'
LABEL_BORDER_LG = '🟨 Redondeado'
LABEL_BORDER_XL = '🟩 Muy redondeado'
LABEL_BORDER_2XL = '🟢 Extra redondeado'
LABEL_BORDER_FULL = '⚪ Círculo completo'

# Sombras
LABEL_SHADOW_NONE = 'Sin sombra'
LABEL_SHADOW_SM = 'Sombra suave'
LABEL_SHADOW_NORMAL = 'Sombra normal'
LABEL_SHADOW_MD = 'Sombra media'
LABEL_SHADOW_LG = 'Sombra grande'
LABEL_SHADOW_XL = 'Sombra extra grande'
LABEL_SHADOW_2XL = 'Sombra masiva'

# Tamaños de botón
LABEL_SIZE_XS = 'Extra pequeño'
LABEL_SIZE_SM = 'Pequeño'
LABEL_SIZE_MD = 'Mediano'
LABEL_SIZE_MD_LG = 'Mediano-grande'
LABEL_SIZE_LG = 'Grande (recomendado)'
LABEL_SIZE_XL = 'Muy grande'
LABEL_SIZE_2XL = 'Extra grande'

# Tamaños de fuente
LABEL_FONT_XS = 'XS - Extra pequeño (0.75rem)'
LABEL_FONT_SM = 'SM - Pequeño (0.875rem)'
LABEL_FONT_BASE = 'Base - Normal (1rem)'
LABEL_FONT_LG = 'LG - Ligeramente grande (1.125rem)'
LABEL_FONT_XL = 'XL - Grande (1.25rem)'
LABEL_FONT_2XL = '2XL - Muy grande (1.5rem)'
LABEL_FONT_3XL = '3XL - Extra grande (1.875rem)'
LABEL_FONT_4XL = '4XL - Gigante (2.25rem)'
LABEL_FONT_5XL = '5XL - Muy gigante (3rem)'
LABEL_FONT_6XL = '6XL - Masivo (3.75rem)'
LABEL_FONT_7XL = '7XL - Épico (4.5rem)'
LABEL_FONT_8XL = '8XL - Colosal (6rem)'

# Altura de línea
LABEL_LINE_COMPACT = 'Compacto (1) - Sin espacio'
LABEL_LINE_TIGHT = 'Apretado (1.2) - Poco espacio'
LABEL_LINE_NORMAL = 'Normal (1.4) - Estándar'
LABEL_LINE_SPACED = 'Espaciado (1.6) - Cómodo'
LABEL_LINE_LOOSE = 'Muy espaciado (1.8) - Aireado'
LABEL_LINE_DOUBLE = 'Doble (2) - Mucho espacio'

# Márgenes
LABEL_MARGIN_NONE = 'Ninguno (0)'
LABEL_MARGIN_XS = 'Muy pequeño (0.25rem)'
LABEL_MARGIN_SM = 'Pequeño (0.5rem)'
LABEL_MARGIN_MD_SM = 'Mediano-pequeño (0.75rem)'
LABEL_MARGIN_MD = 'Normal (1rem)'
LABEL_MARGIN_MD_LG = 'Mediano (1.25rem)'
LABEL_MARGIN_LG = 'Grande (1.5rem)'
LABEL_MARGIN_XL = 'Muy grande (2rem)'
LABEL_MARGIN_2XL = 'Extra grande (2.5rem)'
LABEL_MARGIN_3XL = 'Gigante (3rem)'

# Stock badges
LABEL_STOCK_AVAILABLE = 'Disponible - Verde'
LABEL_STOCK_LOW = 'Bajo stock - Naranja'
LABEL_STOCK_OUT = 'Agotado - Rojo'
LABEL_STOCK_INFO = 'Información - Azul'
LABEL_STOCK_SPECIAL = 'Especial - Púrpura'

# Fuentes
LABEL_FONT_INTER = '🔤 Inter (Moderno)'
LABEL_FONT_ROBOTO = '🔤 Roboto (Versátil)'
LABEL_FONT_POPPINS = '🔤 Poppins (Geométrico)'
LABEL_FONT_MONTSERRAT = '🔤 Montserrat (Elegante)'
LABEL_FONT_OPEN_SANS = '🔤 Open Sans (Legible)'
LABEL_FONT_PLAYFAIR = '✒️ Playfair Display (Clásico)'
LABEL_FONT_MERRIWEATHER = '✒️ Merriweather (Serif)'
LABEL_FONT_OSWALD = '🔤 Oswald (Impactante)'
LABEL_FONT_RALEWAY = '🔤 Raleway (Delicado)'
LABEL_FONT_LATO = '🔤 Lato (Amigable)'

# Pesos de fuente
LABEL_WEIGHT_LIGHT = 'Light (300) - Delgada'
LABEL_WEIGHT_REGULAR = 'Regular (400) - Normal'
LABEL_WEIGHT_MEDIUM = 'Medium (500) - Mediana'
LABEL_WEIGHT_SEMI_BOLD = 'Semi Bold (600) - Seminegrita'
LABEL_WEIGHT_BOLD = 'Bold (700) - Negrita'
LABEL_WEIGHT_EXTRA_BOLD = 'Extra Bold (800) - Extranegrita'
LABEL_WEIGHT_BLACK = 'Black (900) - Negra'

# Alineación
LABEL_ALIGN_CENTER = 'Centrado'
LABEL_ALIGN_LEFT = 'Izquierda'
LABEL_ALIGN_RIGHT = 'Derecha'
LABEL_ALIGN_JUSTIFY = 'Justificado'

# Escala hover
LABEL_SCALE_NONE = 'Sin escala'
LABEL_SCALE_VERY_SUBTLE = 'Muy sutil (2%)'
LABEL_SCALE_SUBTLE = 'Sutil (5% - recomendado)'
LABEL_SCALE_NOTICEABLE = 'Notable (8%)'
LABEL_SCALE_STRONG = 'Fuerte (10%)'
LABEL_SCALE_VERY_STRONG = 'Muy fuerte (15%)'


# =============================================================================
# TIPOGRAFÍA
# =============================================================================

FONT_FAMILY_CHOICES = [
    ("'Inter', sans-serif", LABEL_FONT_INTER),
    ("'Roboto', sans-serif", LABEL_FONT_ROBOTO),
    ("'Poppins', sans-serif", LABEL_FONT_POPPINS),
    ("'Montserrat', sans-serif", LABEL_FONT_MONTSERRAT),
    ("'Open Sans', sans-serif", LABEL_FONT_OPEN_SANS),
    ("'Playfair Display', serif", LABEL_FONT_PLAYFAIR),
    ("'Merriweather', serif", LABEL_FONT_MERRIWEATHER),
    ("'Oswald', sans-serif", LABEL_FONT_OSWALD),
    ("'Raleway', sans-serif", LABEL_FONT_RALEWAY),
    ("'Lato', sans-serif", LABEL_FONT_LATO),
]

FONT_WEIGHT_CHOICES = [
    ('300', LABEL_WEIGHT_LIGHT),
    ('400', LABEL_WEIGHT_REGULAR),
    ('500', LABEL_WEIGHT_MEDIUM),
    ('600', LABEL_WEIGHT_SEMI_BOLD),
    ('700', LABEL_WEIGHT_BOLD),
    ('800', LABEL_WEIGHT_EXTRA_BOLD),
    ('900', LABEL_WEIGHT_BLACK),
]

FONT_SIZE_CHOICES = [
    ('0.75rem', LABEL_FONT_XS),
    ('0.875rem', LABEL_FONT_SM),
    ('1rem', LABEL_FONT_BASE),
    ('1.125rem', LABEL_FONT_LG),
    ('1.25rem', LABEL_FONT_XL),
    ('1.5rem', LABEL_FONT_2XL),
    ('1.875rem', LABEL_FONT_3XL),
    ('2.25rem', LABEL_FONT_4XL),
    ('3rem', LABEL_FONT_5XL),
    ('3.75rem', LABEL_FONT_6XL),
    ('4.5rem', LABEL_FONT_7XL),
    ('6rem', LABEL_FONT_8XL),
]

LINE_HEIGHT_CHOICES = [
    ('1', LABEL_LINE_COMPACT),
    ('1.2', LABEL_LINE_TIGHT),
    ('1.4', LABEL_LINE_NORMAL),
    ('1.6', LABEL_LINE_SPACED),
    ('1.8', LABEL_LINE_LOOSE),
    ('2', LABEL_LINE_DOUBLE),
]

MARGIN_CHOICES = [
    ('0', LABEL_MARGIN_NONE),
    ('0.25rem', LABEL_MARGIN_XS),
    ('0.5rem', LABEL_MARGIN_SM),
    ('0.75rem', LABEL_MARGIN_MD_SM),
    ('1rem', LABEL_MARGIN_MD),
    ('1.25rem', LABEL_MARGIN_MD_LG),
    ('1.5rem', LABEL_MARGIN_LG),
    ('2rem', LABEL_MARGIN_XL),
    ('2.5rem', LABEL_MARGIN_2XL),
    ('3rem', LABEL_MARGIN_3XL),
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
    ('#1a1a1a', LABEL_BLACK),
    ('#c1121f', 'Rojo intenso'),
    ('#00b4d8', 'Azul claro'),
    ('#40916c', 'Verde claro'),
    ('#9c7e2c', 'Dorado oscuro'),
    ('#e76f51', 'Terracota'),
    ('#495057', LABEL_DARK_GRAY),
]

BACKGROUND_COLORS = [
    ('#ffffff', 'Blanco'),
    ('#fafafa', 'Gris muy claro'),
    ('#f0f8ff', 'Azul muy claro'),
    ('#f4f1de', 'Crema'),
    ('#1a1a1a', LABEL_BLACK),
    ('#2d3436', LABEL_DARK_GRAY),
    ('#fdf6e3', 'Beige'),
]

TEXT_COLORS = [
    ('#1a1a1a', LABEL_BLACK),
    ('#2d2d2d', LABEL_DARK_GRAY),
    ('#1d3557', 'Azul noche'),
    ('#03045e', 'Azul profundo'),
    ('#212529', 'Gris carbón'),
    ('#f5f5f5', 'Blanco (fondo oscuro)'),
    ('#e0e0e0', 'Gris claro (fondo oscuro)'),
]


# =============================================================================
# BOTONES
# =============================================================================

BUTTON_BG_CHOICES = [
    ('bg-zicada-accent', LABEL_RED),
    ('bg-black', LABEL_BLACK),
    ('bg-white', LABEL_WHITE),
    ('bg-gray-800', LABEL_DARK_GRAY),
    ('bg-gray-100', LABEL_LIGHT_GRAY),
    ('bg-blue-600', LABEL_BLUE),
    ('bg-green-600', LABEL_GREEN),
    ('bg-purple-600', LABEL_PURPLE),
    ('bg-amber-600', LABEL_AMBER),
    ('bg-transparent', LABEL_TRANSPARENT),
]

BUTTON_HOVER_CHOICES = [
    ('hover:bg-red-700', LABEL_RED_DARKER),
    ('hover:bg-gray-700', LABEL_BLACK_DARKER),
    ('hover:bg-gray-100', LABEL_LIGHT_GRAY),
    ('hover:bg-gray-900', LABEL_DARK_INTENSE),
    ('hover:bg-blue-700', LABEL_BLUE_DARKER),
    ('hover:bg-green-700', LABEL_GREEN_DARKER),
    ('hover:bg-purple-700', LABEL_PURPLE_DARKER),
    ('hover:bg-amber-700', LABEL_AMBER_DARKER),
    ('hover:bg-white', LABEL_WHITE),
    ('hover:bg-opacity-90', LABEL_OPACITY_90),
    ('hover:scale-105', LABEL_SCALE_5),
    ('hover:scale-110', LABEL_SCALE_10),
]

BUTTON_TEXT_COLOR_CHOICES = [
    ('text-white', LABEL_WHITE),
    ('text-gray-900', LABEL_BLACK),
    ('text-gray-700', LABEL_DARK_GRAY),
    ('text-gray-500', '🌫️ Gris medio'),
    ('text-zicada-accent', LABEL_RED),
    ('text-blue-600', LABEL_BLUE),
]

BUTTON_BORDER_RADIUS_CHOICES = [
    ('rounded-none', LABEL_BORDER_NONE),
    ('rounded-sm', LABEL_BORDER_SM),
    ('rounded-md', LABEL_BORDER_MD),
    ('rounded-lg', LABEL_BORDER_LG),
    ('rounded-xl', LABEL_BORDER_XL),
    ('rounded-2xl', LABEL_BORDER_2XL),
    ('rounded-full', LABEL_BORDER_FULL),
]

BUTTON_SIZE_CHOICES = [
    ('px-2 py-1 text-xs', LABEL_SIZE_XS),
    ('px-3 py-1.5 text-sm', LABEL_SIZE_SM),
    ('px-4 py-2 text-base', LABEL_SIZE_MD),
    ('px-6 py-2.5 text-base', LABEL_SIZE_MD_LG),
    ('px-8 py-3 text-lg', LABEL_SIZE_LG),
    ('px-10 py-4 text-xl', LABEL_SIZE_XL),
    ('px-12 py-5 text-2xl', LABEL_SIZE_2XL),
]

BUTTON_SHADOW_CHOICES = [
    ('shadow-none', LABEL_SHADOW_NONE),
    ('shadow-sm', LABEL_SHADOW_SM),
    ('shadow', LABEL_SHADOW_NORMAL),
    ('shadow-md', LABEL_SHADOW_MD),
    ('shadow-lg', LABEL_SHADOW_LG),
    ('shadow-xl', LABEL_SHADOW_XL),
    ('shadow-2xl', LABEL_SHADOW_2XL),
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
    ('center', LABEL_ALIGN_CENTER),
    ('left', LABEL_ALIGN_LEFT),
    ('right', LABEL_ALIGN_RIGHT),
    ('justify', LABEL_ALIGN_JUSTIFY),
]

SECTION_HEIGHT_CHOICES = [(f'{i}vh', f'{i}% de la pantalla') for i in range(10, 101, 10)]


# =============================================================================
# TARJETAS
# =============================================================================

CARD_BORDER_RADIUS_CHOICES = BUTTON_BORDER_RADIUS_CHOICES
CARD_SHADOW_CHOICES = BUTTON_SHADOW_CHOICES

CARD_HOVER_SCALE_CHOICES = [
    ('1.00', LABEL_SCALE_NONE),
    ('1.02', LABEL_SCALE_VERY_SUBTLE),
    ('1.05', LABEL_SCALE_SUBTLE),
    ('1.08', LABEL_SCALE_NOTICEABLE),
    ('1.10', LABEL_SCALE_STRONG),
    ('1.15', LABEL_SCALE_VERY_STRONG),
]


# =============================================================================
# BADGES
# =============================================================================

STOCK_BADGE_COLORS = [
    ('bg-green-100 text-green-700', LABEL_STOCK_AVAILABLE),
    ('bg-orange-100 text-orange-700', LABEL_STOCK_LOW),
    ('bg-red-100 text-red-700', LABEL_STOCK_OUT),
    ('bg-blue-100 text-blue-700', LABEL_STOCK_INFO),
    ('bg-purple-100 text-purple-700', LABEL_STOCK_SPECIAL),
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