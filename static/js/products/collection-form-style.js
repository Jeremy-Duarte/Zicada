// ============================================
// COLLECTION STYLE FORM - JavaScript
// Estilos de colección con preview en vivo
// ============================================

(function() {
    'use strict';

    // Paletas de colores predefinidas
    const colorPalettes = {
        'zicada': { primary: '#c2a575', secondary: '#8b5e3c', background: '#ffffff', text: '#1a1a1a' },
        'elegant': { primary: '#2d2d2d', secondary: '#1a1a1a', background: '#fafafa', text: '#2d2d2d' },
        'vibrant': { primary: '#e63946', secondary: '#c1121f', background: '#ffffff', text: '#1d3557' },
        'ocean': { primary: '#0077b6', secondary: '#00b4d8', background: '#f0f8ff', text: '#03045e' },
        'nature': { primary: '#2d6a4f', secondary: '#40916c', background: '#f4f1de', text: '#1b4332' },
        'luxury': { primary: '#d4af37', secondary: '#9c7e2c', background: '#1a1a1a', text: '#f5f5f5' },
        'pastel': { primary: '#f4a261', secondary: '#e76f51', background: '#fdf6e3', text: '#2d3436' },
        'minimal': { primary: '#6c757d', secondary: '#495057', background: '#ffffff', text: '#212529' },
        'dark': { primary: '#c2a575', secondary: '#8b5e3c', background: '#1a1a1a', text: '#f5f5f5' },
        'fresh': { primary: '#2ecc71', secondary: '#27ae60', background: '#ffffff', text: '#2c3e50' }
    };

    // Efectos predefinidos con CSS
    const effectStyles = {
        'none': '',
        'zoom_fade': `.mock-product-card { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); opacity: 0; animation: fadeIn 0.5s ease forwards; } .mock-product-card:hover { transform: scale(1.05); box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); } @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }`,
        'lift_slide': `.mock-product-card { transition: all 0.3s ease; animation: slideInUp 0.5s ease forwards; } .mock-product-card:hover { transform: translateY(-8px); box-shadow: 0 25px 30px -12px rgba(0,0,0,0.25); } @keyframes slideInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }`,
        'glow_premium': `.mock-product-card { transition: all 0.3s ease; animation: fadeInUp 0.6s ease forwards; } .mock-product-card:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(194,165,117,0.4); } @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }`,
        'parallax_scroll': `.mock-product-card { transition: all 0.3s ease; animation: fadeIn 0.8s ease forwards; overflow: hidden; position: relative; } .mock-product-card::before { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); transition: left 0.5s ease; } .mock-product-card:hover::before { left: 100%; } @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }`,
        'explosion': `.mock-product-card { transition: all 0.2s cubic-bezier(0.68, -0.55, 0.265, 1.55); animation: zoomIn 0.4s ease forwards; } .mock-product-card:hover { transform: scale(1.1); box-shadow: 0 30px 40px -15px rgba(0,0,0,0.3); } @keyframes zoomIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }`,
        'soft_shadow': `.mock-product-card { transition: all 0.3s ease; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); } .mock-product-card:hover { transform: translateY(-4px); box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }`,
        'cinematic': `.mock-product-card { transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1); animation: slideInLeft 0.7s ease forwards; overflow: hidden; position: relative; } .mock-product-card::after { content: ''; position: absolute; inset: 0; background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.1) 50%, transparent 100%); transform: translateX(-100%); transition: transform 0.6s ease; } .mock-product-card:hover::after { transform: translateX(100%); } .mock-product-card:hover { transform: scale(1.03); box-shadow: 0 25px 30px -12px rgba(0,0,0,0.3); } @keyframes slideInLeft { from { opacity: 0; transform: translateX(-30px); } to { opacity: 1; transform: translateX(0); } }`
    };

    const effectNames = {
        'none': 'Sin efectos',
        'zoom_fade': 'Zoom + Fade',
        'lift_slide': 'Levitar + Slide',
        'glow_premium': 'Glow Premium',
        'parallax_scroll': 'Parallax + Partículas',
        'explosion': 'Explosión Dinámica',
        'soft_shadow': 'Sombra Suave',
        'cinematic': 'Cinemático'
    };

    let currentEffect = 'none';
    let currentBgObjectUrl = null;

    // ============================================
    // FUNCIONES AUXILIARES
    // ============================================

    function getBackgroundImageUrl() {
        const bgInput = document.querySelector('#id_background_image');
        const file = bgInput?.files?.[0];
        if (file) {
            if (currentBgObjectUrl) URL.revokeObjectURL(currentBgObjectUrl);
            currentBgObjectUrl = URL.createObjectURL(file);
            return currentBgObjectUrl;
        }
        const currentImg = document.getElementById('current-bg-image');
        return currentImg?.src || '';
    }

    function updatePalettePreview(palette) {
        const previewContainer = document.getElementById('palette-preview');
        const circles = previewContainer?.querySelectorAll('.rounded-full');
        if (circles?.length >= 4) {
            circles[0].style.backgroundColor = palette.primary;
            circles[1].style.backgroundColor = palette.secondary;
            circles[2].style.backgroundColor = palette.background;
            circles[3].style.backgroundColor = palette.text;
        }
    }

    function applyColorPalette(paletteKey) {
        const palette = colorPalettes[paletteKey];
        if (!palette) return;

        const primaryInput = document.querySelector('#id_primary_color');
        const secondaryInput = document.querySelector('#id_secondary_color');
        const backgroundInput = document.querySelector('#id_background_color');
        const textInput = document.querySelector('#id_text_color');

        if (primaryInput) primaryInput.value = palette.primary;
        if (secondaryInput) secondaryInput.value = palette.secondary;
        if (backgroundInput) backgroundInput.value = palette.background;
        if (textInput) textInput.value = palette.text;

        primaryInput?.dispatchEvent(new Event('input'));
        secondaryInput?.dispatchEvent(new Event('input'));
        backgroundInput?.dispatchEvent(new Event('input'));
        textInput?.dispatchEvent(new Event('input'));

        updatePalettePreview(palette);
        updateColorPreviews();
    }

    function applyEffectToPreview(effectKey) {
        currentEffect = effectKey;
        const previewCard = document.querySelector('#effect-preview-card .rounded-xl');
        previewCard?.classList.remove('mock-product-card');
        setTimeout(() => previewCard?.classList.add('mock-product-card'), 10);
        const effectNameElement = document.getElementById('current-effect-name');
        if (effectNameElement) effectNameElement.textContent = effectNames[effectKey] || 'Sin efectos';
        updatePreviewFrame();
    }

    function generateCollectionPreview() {
        const primaryColor = document.querySelector('#id_primary_color')?.value || '#c2a575';
        const secondaryColor = document.querySelector('#id_secondary_color')?.value || '#8b5e3c';
        const backgroundColor = document.querySelector('#id_background_color')?.value || '#ffffff';
        const textColor = document.querySelector('#id_text_color')?.value || '#1a1a1a';
        const titleFont = document.querySelector('#id_title_font')?.value || "'Inter', sans-serif";
        const bgImageUrl = getBackgroundImageUrl();

        const cardBgColor = document.querySelector('#id_card_background_color')?.value || backgroundColor;
        const cardTitleColor = document.querySelector('#id_card_title_color')?.value || primaryColor;
        const cardPriceColor = document.querySelector('#id_card_price_color')?.value || primaryColor;
        const cardBorderRadius = document.querySelector('#id_card_border_radius')?.value || '0.5rem';
        const cardShadow = document.querySelector('#id_card_shadow')?.value || '0 1px 3px 0 rgba(0,0,0,0.1)';
        const cardHoverScale = document.querySelector('#id_card_hover_scale')?.value || '1.05';
        const showCategory = document.querySelector('#id_card_show_category')?.checked || false;
        const showStockBadge = document.querySelector('#id_card_show_stock_badge')?.checked || false;
        const customCss = document.querySelector('#id_custom_css')?.value || '';

        const effectCss = effectStyles[currentEffect] || '';

        const mockProducts = [
            { name: "Camiseta Esencial", price: "49,900", category: "Camisetas", stock: "available" },
            { name: "Hoodie Premium", price: "129,900", category: "Hoodies", stock: "available" },
            { name: "Pantalón Jogger", price: "89,900", category: "Pantalones", stock: "low" },
            { name: "Gorra Urbana", price: "39,900", category: "Accesorios", stock: "available" }
        ];

        const stockBadgeText = { 'available': 'Disponible', 'low': '¡Últimas unidades!', 'out': 'Agotado' };
        const stockBadgeClass = { 'available': 'bg-green-100 text-green-700', 'low': 'bg-orange-100 text-orange-700', 'out': 'bg-red-100 text-red-700' };

        let productsHtml = '';
        mockProducts.forEach(product => {
            productsHtml += `
                <div class="mock-product-card rounded-xl overflow-hidden shadow-lg" style="background-color: ${cardBgColor}; border-radius: ${cardBorderRadius}; box-shadow: ${cardShadow};">
                    <div class="h-40 bg-gray-200 relative">
                        <div class="absolute inset-0 flex items-center justify-center text-gray-400"><i class="fas fa-image text-2xl"></i></div>
                    </div>
                    <div class="p-3">
                        <h4 class="font-semibold text-base" style="color: ${cardTitleColor};">${product.name}</h4>
                        ${showCategory ? `<p class="text-xs text-gray-500">${product.category}</p>` : ''}
                        <div class="flex justify-between items-center mt-2">
                            <span class="text-lg font-bold" style="color: ${cardPriceColor};">$${product.price}</span>
                            ${showStockBadge ? `<span class="text-xs px-2 py-0.5 rounded-full ${stockBadgeClass[product.stock]}">${stockBadgeText[product.stock]}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });

        const collectionNameElement = document.querySelector('h1.text-2xl');
        const collectionName = collectionNameElement?.textContent?.replace('Estilos de ', '') || 'Colección';
        const collectionDescElement = document.querySelector('p.text-gray-500.mt-1');
        const collectionDesc = collectionDescElement?.textContent || 'Colección exclusiva';

        return `
            <style>
                .collection-preview {
                    background-color: ${backgroundColor};
                    ${bgImageUrl ? `background-image: url('${bgImageUrl}'); background-size: cover; background-position: center;` : ''}
                    color: ${textColor};
                    min-height: 100%;
                    padding: 20px;
                }
                .collection-preview h1 { font-family: ${titleFont}; color: ${primaryColor}; }
                .btn-preview { background-color: ${primaryColor}; color: white; padding: 8px 20px; border-radius: 8px; display: inline-block; text-decoration: none; }
                .btn-preview:hover { background-color: ${secondaryColor}; }
                .mock-product-card { transition: transform 0.3s ease; }
                .mock-product-card:hover { transform: scale(${cardHoverScale}); }
                ${effectCss}
                ${customCss}
            </style>
            <div class="collection-preview">
                <div class="text-center mb-6">
                    <h1 class="text-3xl font-bold">${collectionName}</h1>
                    <p class="text-gray-600 mt-2">${collectionDesc}</p>
                    <div class="mt-4"><a href="#" class="btn-preview">Ver catálogo</a></div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">${productsHtml}</div>
            </div>
        `;
    }

    function updateColorPreviews() {
        const primary = document.querySelector('#id_primary_color')?.value || '#c2a575';
        const secondary = document.querySelector('#id_secondary_color')?.value || '#8b5e3c';
        const background = document.querySelector('#id_background_color')?.value || '#ffffff';
        const text = document.querySelector('#id_text_color')?.value || '#1a1a1a';

        const primaryPreview = document.getElementById('primary-color-preview');
        const secondaryPreview = document.getElementById('secondary-color-preview');
        const backgroundPreview = document.getElementById('background-color-preview');
        const textPreview = document.getElementById('text-color-preview');

        if (primaryPreview) primaryPreview.style.backgroundColor = primary;
        if (secondaryPreview) secondaryPreview.style.backgroundColor = secondary;
        if (backgroundPreview) backgroundPreview.style.backgroundColor = background;
        if (textPreview) textPreview.style.backgroundColor = text;

        const cardBg = document.querySelector('#id_card_background_color')?.value || background;
        const cardTitle = document.querySelector('#id_card_title_color')?.value || primary;
        const cardPrice = document.querySelector('#id_card_price_color')?.value || primary;

        const cardBgPreview = document.getElementById('card-bg-preview');
        const cardTitlePreview = document.getElementById('card-title-color-preview');
        const cardPricePreview = document.getElementById('card-price-color-preview');

        if (cardBgPreview) cardBgPreview.style.backgroundColor = cardBg;
        if (cardTitlePreview) cardTitlePreview.style.backgroundColor = cardTitle;
        if (cardPricePreview) cardPricePreview.style.backgroundColor = cardPrice;

        updatePreviewFrame();
    }

    function updateFontPreviews() {
        const selectedFont = document.querySelector('#id_title_font')?.value || "'Inter', sans-serif";
        const fontSize = document.getElementById('preview-font-size')?.value || '2rem';

        const collectionTitlePreview = document.getElementById('collection-title-preview');
        if (collectionTitlePreview) {
            collectionTitlePreview.style.fontFamily = selectedFont;
            collectionTitlePreview.style.fontSize = fontSize;
        }

        const customPreview = document.getElementById('custom-font-preview');
        if (customPreview) {
            customPreview.style.fontFamily = selectedFont;
            customPreview.style.fontSize = fontSize;
        }

        const customText = document.getElementById('custom-preview-text')?.value;
        if (customPreview && customText) customPreview.textContent = customText;
    }

    function updatePreviewFrame() {
        const container = document.getElementById('dynamic-preview');
        if (container) container.innerHTML = generateCollectionPreview();

        const expandedContainer = document.getElementById('expanded-preview-container');
        const modal = document.getElementById('live-preview-modal');
        if (expandedContainer && modal?.classList.contains('active')) {
            expandedContainer.innerHTML = generateCollectionPreview();
        }
    }

    function resetFontPreview() {
        const customPreview = document.getElementById('custom-font-preview');
        if (customPreview) {
            customPreview.style.fontSize = '';
            customPreview.style.fontWeight = '';
            customPreview.style.fontStyle = '';
            customPreview.style.letterSpacing = '';
        }
        const fontSizeSelect = document.getElementById('preview-font-size');
        if (fontSizeSelect) fontSizeSelect.value = '2rem';
        updateFontPreviews();
    }

    function openExpandedPreview() {
        const modal = document.getElementById('live-preview-modal');
        const expandedContainer = document.getElementById('expanded-preview-container');
        if (modal && expandedContainer) {
            expandedContainer.innerHTML = generateCollectionPreview();
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeExpandedPreview() {
        const modal = document.getElementById('live-preview-modal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    function toggleAdvanced() {
        const content = document.getElementById('advanced-content');
        const icon = document.getElementById('advanced-toggle-icon');
        if (content && icon) {
            content.classList.toggle('hidden');
            icon.classList.toggle('fa-chevron-down');
            icon.classList.toggle('fa-chevron-up');
        }
    }

    document.querySelector('[data-toggle="advanced"]')?.addEventListener('click', toggleAdvanced);

    // ============================================
    // EVENTOS DE PALETA DE COLORES
    // ============================================

    function initPaletteEvents() {
        const applyPaletteBtn = document.getElementById('apply-palette');
        applyPaletteBtn?.addEventListener('click', () => {
            const select = document.getElementById('color-palette-selector');
            if (select?.value) {
                applyColorPalette(select.value);
                showTemporarySuccess(applyPaletteBtn, 'Aplicado!');
            }
        });

        const resetColorsBtn = document.getElementById('reset-colors');
        resetColorsBtn?.addEventListener('click', () => {
            applyColorPalette('zicada');
            const paletteSelect = document.getElementById('color-palette-selector');
            if (paletteSelect) paletteSelect.value = 'zicada';
            showTemporarySuccess(resetColorsBtn, 'Restablecido!');
        });

        const paletteSelector = document.getElementById('color-palette-selector');
        paletteSelector?.addEventListener('change', function() {
            const selectedPalette = this.value;
            if (selectedPalette && colorPalettes[selectedPalette]) {
                updatePalettePreview(colorPalettes[selectedPalette]);
            }
        });
    }

    // ============================================
    // EVENTOS DE EFECTOS
    // ============================================

    function initEffectEvents() {
        const applyEffectBtn = document.getElementById('apply-effect');
        applyEffectBtn?.addEventListener('click', () => {
            const select = document.getElementById('effect-preset-selector');
            if (select?.value) {
                applyEffectToPreview(select.value);
                showTemporarySuccess(applyEffectBtn, 'Aplicado!');
            }
        });
    }

    // ============================================
    // EVENTOS DE PREVIEW
    // ============================================

    function initPreviewEvents() {
        const refreshBtn = document.getElementById('refresh-preview');
        refreshBtn?.addEventListener('click', updatePreviewFrame);

        const expandBtn = document.getElementById('expand-preview');
        expandBtn?.addEventListener('click', openExpandedPreview);

        const closeModalBtn = document.getElementById('close-preview-modal');
        closeModalBtn?.addEventListener('click', closeExpandedPreview);
    }

    // ============================================
    // EVENTOS DE TIPOGRAFÍA
    // ============================================

    function initTypographyEvents() {
        const fontSizeSelect = document.getElementById('preview-font-size');
        fontSizeSelect?.addEventListener('change', updateFontPreviews);

        const resetFontBtn = document.getElementById('reset-font-preview');
        resetFontBtn?.addEventListener('click', resetFontPreview);

        const customTextInput = document.getElementById('custom-preview-text');
        customTextInput?.addEventListener('input', (e) => {
            const customPreview = document.getElementById('custom-font-preview');
            if (customPreview) {
                customPreview.textContent = e.target.value || 'Texto personalizable para probar la fuente';
            }
        });

        document.querySelectorAll('.font-style-preset').forEach(btn => {
            btn.addEventListener('click', function() {
                const customPreview = document.getElementById('custom-font-preview');
                if (customPreview) {
                    if (this.dataset.fontSize) customPreview.style.fontSize = this.dataset.fontSize;
                    if (this.dataset.fontWeight) customPreview.style.fontWeight = this.dataset.fontWeight;
                    if (this.dataset.fontStyle) customPreview.style.fontStyle = this.dataset.fontStyle;
                    if (this.dataset.letterSpacing) customPreview.style.letterSpacing = this.dataset.letterSpacing;
                }
            });
        });
    }

    // ============================================
    // EVENTOS DE IMAGEN DE FONDO
    // ============================================

    function initBackgroundImageEvents() {
        const bgImageInput = document.querySelector('#id_background_image');
        bgImageInput?.addEventListener('change', () => {
            updatePreviewFrame();
            const previewContainer = document.getElementById('bg-image-preview');
            const previewImg = document.getElementById('bg-image-preview-img');
            const file = bgImageInput.files?.[0];
            if (file && previewContainer && previewImg) {
                const reader = new FileReader();
                reader.onload = (event) => { previewImg.src = event.target.result; };
                reader.readAsDataURL(file);
                previewContainer.classList.remove('hidden');
            }
        });

        const removeBgBtn = document.getElementById('remove-bg-image');
        removeBgBtn?.addEventListener('click', () => {
            clearBackgroundImage();
        });

        const clearPreviewBtn = document.getElementById('clear-bg-preview');
        clearPreviewBtn?.addEventListener('click', () => {
            clearBackgroundImage();
        });
    }

    function clearBackgroundImage() {
        const bgInput = document.querySelector('#id_background_image');
        if (bgInput) bgInput.value = '';
        if (currentBgObjectUrl) {
            URL.revokeObjectURL(currentBgObjectUrl);
            currentBgObjectUrl = null;
        }
        const previewContainer = document.getElementById('bg-image-preview');
        previewContainer?.classList.add('hidden');
        updatePreviewFrame();
    }

    // ============================================
    // EVENTOS DE FONDO DE PRUEBA
    // ============================================

    function initBgPreviewEvents() {
        document.querySelectorAll('.bg-preview-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const fontPreviewCard = document.querySelector('.font-preview-card');
                if (fontPreviewCard) {
                    fontPreviewCard.style.backgroundColor = this.dataset.bgColor;
                    fontPreviewCard.querySelectorAll('div[id$="-preview"]').forEach(el => {
                        el.style.color = this.dataset.textColor;
                    });
                }
            });
        });
    }

    // ============================================
    // EVENTOS DEL FORMULARIO
    // ============================================

    function initFormEvents() {
        const form = document.getElementById('style-form');
        const updateHandler = () => {
            updateColorPreviews();
            updateFontPreviews();
        };
        form?.querySelectorAll('input, select, textarea').forEach(el => {
            el.addEventListener('input', updateHandler);
            el.addEventListener('change', updateHandler);
        });
    }

    // ============================================
    // EVENTOS DE NAVEGACIÓN
    // ============================================

    function initNavigationEvents() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                    link.classList.add('active');
                }
            });
        });
    }

    // ============================================
    // EVENTOS DEL MODAL
    // ============================================

    function initModalEvents() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeExpandedPreview();
        });
        const modal = document.getElementById('live-preview-modal');
        modal?.addEventListener('click', (e) => {
            if (e.target === modal) closeExpandedPreview();
        });
    }

    // ============================================
    // FUNCIÓN AUXILIAR
    // ============================================

    function showTemporarySuccess(element, message) {
        const originalText = element.innerHTML;
        element.innerHTML = `<i class="fas fa-check mr-1"></i> ${message}`;
        setTimeout(() => { element.innerHTML = originalText; }, 1500);
    }

    // ============================================
    // INICIALIZACIÓN PRINCIPAL
    // ============================================

    function initEventListeners() {
        initPaletteEvents();
        initEffectEvents();
        initPreviewEvents();
        initTypographyEvents();
        initBackgroundImageEvents();
        initBgPreviewEvents();
        initFormEvents();
        initNavigationEvents();
        initModalEvents();
    }

    function init() {
        updateColorPreviews();
        updateFontPreviews();
        applyEffectToPreview('none');
        const effectSelect = document.getElementById('effect-preset-selector');
        if (effectSelect) effectSelect.value = 'none';
        const primary = document.querySelector('#id_primary_color')?.value || '#c2a575';
        const secondary = document.querySelector('#id_secondary_color')?.value || '#8b5e3c';
        const background = document.querySelector('#id_background_color')?.value || '#ffffff';
        const text = document.querySelector('#id_text_color')?.value || '#1a1a1a';
        updatePalettePreview({ primary, secondary, background, text });
        initEventListeners();
    }

    globalThis.toggleAdvanced = toggleAdvanced;
    globalThis.CollectionStyleForm = {
        updatePreviewFrame,
        applyColorPalette,
        applyEffectToPreview
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();