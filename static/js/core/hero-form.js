const opacityInput = document.querySelector('#id_overlay_opacity');
const opacitySlider = document.getElementById('overlay-opacity-slider');
if (opacityInput && opacitySlider) {
    opacitySlider.addEventListener('input', function() { opacityInput.value = this.value; updatePreview(); });
    opacityInput.addEventListener('input', function() { opacitySlider.value = this.value; updatePreview(); });
}

function getOpacityClass(opacity) {
    if (opacity >= 0.9) return 'bg-opacity-90';
    if (opacity >= 0.8) return 'bg-opacity-80';
    if (opacity >= 0.7) return 'bg-opacity-70';
    if (opacity >= 0.6) return 'bg-opacity-60';
    if (opacity >= 0.5) return 'bg-opacity-50';
    if (opacity >= 0.4) return 'bg-opacity-40';
    if (opacity >= 0.3) return 'bg-opacity-30';
    if (opacity >= 0.2) return 'bg-opacity-20';
    if (opacity >= 0.1) return 'bg-opacity-10';
    return 'bg-opacity-0';
}

function updateOverlayPreview() {
    const opacity = Number.parseFloat(document.querySelector('#id_overlay_opacity')?.value) || 0.3;
    const overlayDiv = document.getElementById('overlay-preview-overlay');
    if (overlayDiv) {
        overlayDiv.classList.remove('bg-opacity-0', 'bg-opacity-10', 'bg-opacity-20', 'bg-opacity-30', 'bg-opacity-40', 'bg-opacity-50', 'bg-opacity-60', 'bg-opacity-70', 'bg-opacity-80', 'bg-opacity-90');
        overlayDiv.classList.add(getOpacityClass(opacity));
    }
}

function updateTitlePreview() {
    const bgColor = document.getElementById('preview-bg-color')?.value || '#f5f5f5';
    const textColor = document.querySelector('#id_title_color')?.value || '#ffffff';
    const titleText = document.querySelector('#id_title_text')?.value || 'ZICADA';
    const titleFontFamily = document.querySelector('#id_title_font_family')?.value || "'Inter', sans-serif";
    const titleFontSize = document.querySelector('#id_title_font_size')?.value || '1.5rem';
    const titleFontWeight = document.querySelector('#id_title_font_weight')?.value || '600';
    const titleLineHeight = document.querySelector('#id_title_line_height')?.value || '1.4';
    const titleMarginBottom = document.querySelector('#id_title_margin_bottom')?.value || '0';
    const titlePreviewDiv = document.getElementById('title-preview-container');
    const titleTextSpan = document.getElementById('title-preview-text');
    if (titlePreviewDiv) titlePreviewDiv.style.backgroundColor = bgColor;
    if (titleTextSpan) {
        titleTextSpan.style.fontFamily = titleFontFamily;
        titleTextSpan.style.fontSize = titleFontSize;
        titleTextSpan.style.fontWeight = titleFontWeight;
        titleTextSpan.style.lineHeight = titleLineHeight;
        titleTextSpan.style.color = textColor;
        titleTextSpan.style.marginBottom = titleMarginBottom;
        titleTextSpan.textContent = titleText;
    }
}

function updateSubtitlePreview() {
    const bgColor = document.getElementById('preview-bg-color')?.value || '#f5f5f5';
    const textColor = document.querySelector('#id_subtitle_color')?.value || '#666';
    const subtitleText = document.querySelector('#id_subtitle_text')?.value || 'LA MODA SE VA, TU ESTILO PERMANECE';
    const subtitleFontFamily = document.querySelector('#id_subtitle_font_family')?.value || "'Inter', sans-serif";
    const subtitleFontSize = document.querySelector('#id_subtitle_font_size')?.value || '1rem';
    const subtitleFontWeight = document.querySelector('#id_subtitle_font_weight')?.value || '400';
    const subtitleLineHeight = document.querySelector('#id_subtitle_line_height')?.value || '1.4';
    const subtitleMarginBottom = document.querySelector('#id_subtitle_margin_bottom')?.value || '0';
    const subtitlePreviewDiv = document.getElementById('subtitle-preview-container');
    const subtitleTextSpan = document.getElementById('subtitle-preview-text');
    if (subtitlePreviewDiv) subtitlePreviewDiv.style.backgroundColor = bgColor;
    if (subtitleTextSpan) {
        subtitleTextSpan.style.fontFamily = subtitleFontFamily;
        subtitleTextSpan.style.fontSize = subtitleFontSize;
        subtitleTextSpan.style.fontWeight = subtitleFontWeight;
        subtitleTextSpan.style.lineHeight = subtitleLineHeight;
        subtitleTextSpan.style.color = textColor;
        subtitleTextSpan.style.marginBottom = subtitleMarginBottom;
        subtitleTextSpan.textContent = subtitleText;
    }
}

function getInputValue(selector, defaultValue = '') {
    return document.querySelector(selector)?.value || defaultValue;
}

function getInputNumber(selector, defaultValue = 0.3) {
    const value = document.querySelector(selector)?.value;
    return value !== undefined && value !== '' ? Number.parseFloat(value) : defaultValue;
}

function getCheckedValue(selector, defaultValue = 'center') {
    return document.querySelector(selector)?.value || defaultValue;
}

function updateTitlePreviewElement() {
    const titleEl = document.getElementById('preview-title');
    if (!titleEl) return;
    
    titleEl.textContent = getInputValue('#id_title_text', 'ZICADA');
    titleEl.style.fontFamily = getInputValue('#id_title_font_family', "'Inter', sans-serif");
    titleEl.style.fontSize = getInputValue('#id_title_font_size', '4rem');
    titleEl.style.fontWeight = getInputValue('#id_title_font_weight', '800');
    titleEl.style.lineHeight = getInputValue('#id_title_line_height', '1.2');
    titleEl.style.color = getInputValue('#id_title_color', '#ffffff');
    titleEl.style.marginBottom = getInputValue('#id_title_margin_bottom', '1.5rem');
}

function updateSubtitlePreviewElement() {
    const subtitleEl = document.getElementById('preview-subtitle');
    if (!subtitleEl) return;
    
    subtitleEl.textContent = getInputValue('#id_subtitle_text', '');
    subtitleEl.style.fontFamily = getInputValue('#id_subtitle_font_family', "'Inter', sans-serif");
    subtitleEl.style.fontSize = getInputValue('#id_subtitle_font_size', '1.25rem');
    subtitleEl.style.fontWeight = getInputValue('#id_subtitle_font_weight', '400');
    subtitleEl.style.lineHeight = getInputValue('#id_subtitle_line_height', '1.5');
    subtitleEl.style.color = getInputValue('#id_subtitle_color', '#e5e5e5');
    subtitleEl.style.marginBottom = getInputValue('#id_subtitle_margin_bottom', '2.5rem');
}

function updateOverlayPreviewElement() {
    const opacity = getInputNumber('#id_overlay_opacity', 0.3);
    const overlayDiv = document.getElementById('preview-overlay');
    if (!overlayDiv) return;
    
    const opacityClasses = ['bg-opacity-0', 'bg-opacity-10', 'bg-opacity-20', 'bg-opacity-30', 'bg-opacity-40', 'bg-opacity-50', 'bg-opacity-60', 'bg-opacity-70', 'bg-opacity-80', 'bg-opacity-90'];
    overlayDiv.classList.remove(...opacityClasses);
    overlayDiv.classList.add(getOpacityClass(opacity));
}

function updateAlignment() {
    const alignment = getCheckedValue('input[name="content_alignment"]:checked', 'center');
    const contentDiv = document.getElementById('preview-content');
    const buttonWrapper = document.getElementById('preview-button-wrapper');
    
    if (contentDiv) {
        contentDiv.classList.remove('text-left', 'text-center', 'text-right');
        contentDiv.classList.add(`text-${alignment}`);
    }
    
    if (buttonWrapper) {
        buttonWrapper.classList.remove('justify-start', 'justify-center', 'justify-end');
        const alignmentMap = { left: 'justify-start', center: 'justify-center', right: 'justify-end' };
        buttonWrapper.classList.add(alignmentMap[alignment] || 'justify-center');
    }
}

function safeUrl(result) {
    return result ? `url(${result})` : '';
}

function updateBackgroundImage() {
    const fileInput = document.querySelector('#id_background_image');
    const currentImage = '{{ background_image_url|default:"" }}';
    const previewBg = document.getElementById('preview-bg');
    const overlayPreviewBg = document.getElementById('overlay-preview-bg');
    
    const hasFile = fileInput?.files?.[0];
    
    if (hasFile) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const imageUrl = safeUrl(e.target?.result);
            if (imageUrl) {
                if (previewBg) previewBg.style.backgroundImage = imageUrl;
                if (overlayPreviewBg) overlayPreviewBg.style.backgroundImage = imageUrl;
            }
        };
        reader.readAsDataURL(fileInput.files[0]);
    } else if (currentImage) {
        const imageUrl = safeUrl(currentImage);
        if (imageUrl) {
            if (previewBg) previewBg.style.backgroundImage = imageUrl;
            if (overlayPreviewBg) overlayPreviewBg.style.backgroundImage = imageUrl;
        }
    }
}

function updateSectionHeight() {
    const sectionHeight = getInputValue('#id_section_height', '100vh');
    const previewContainer = document.getElementById('live-preview');
    if (previewContainer) {
        previewContainer.style.height = sectionHeight;
        previewContainer.style.minHeight = '400px';
    }
}

function updateColorPreviews() {
    const titleColorPreview = document.getElementById('title-color-preview');
    const subtitleColorPreview = document.getElementById('subtitle-color-preview');
    
    if (titleColorPreview) {
        titleColorPreview.style.backgroundColor = getInputValue('#id_title_color');
    }
    if (subtitleColorPreview) {
        subtitleColorPreview.style.backgroundColor = getInputValue('#id_subtitle_color');
    }
}

function updatePreview() {
    updateTitlePreviewElement();
    updateSubtitlePreviewElement();
    updateOverlayPreviewElement();
    updateAlignment();
    updateBackgroundImage();
    updateSectionHeight();
    updateColorPreviews();
    
    if (typeof updateTitlePreview === 'function') updateTitlePreview();
    if (typeof updateSubtitlePreview === 'function') updateSubtitlePreview();
    if (typeof updateButtonPreview === 'function') updateButtonPreview();
    if (typeof updateOverlayPreview === 'function') updateOverlayPreview();
}

function updateButtonPreview() {
    const bg = document.querySelector('#id_button_bg_color')?.value || 'bg-zicada-accent';
    const hover = document.querySelector('#id_button_hover_color')?.value || 'hover:bg-red-700';
    const text = document.querySelector('#id_button_text_color')?.value || 'text-white';
    const rounded = document.querySelector('#id_button_border_radius')?.value || 'rounded-lg';
    const size = document.querySelector('#id_button_size')?.value || 'px-8 py-3 text-lg';
    const shadow = document.querySelector('#id_button_shadow')?.value || 'shadow-lg';
    const width = document.querySelector('#id_button_width')?.value || 'inline-block';
    const buttonText = document.querySelector('#id_button_text')?.value || 'Explorar Catálogo';

    const previewBtn = document.getElementById('preview-button');
    if (previewBtn) {
        previewBtn.className = `${bg} ${hover} ${text} ${rounded} ${size} ${shadow} ${width} font-semibold transition-all duration-300 transform hover:scale-105 inline-block text-center`;
        previewBtn.textContent = buttonText;
    }

    const previewBtnLive = document.getElementById('button-preview');
    if (previewBtnLive) {
        previewBtnLive.className = `${bg} ${hover} ${text} ${rounded} ${size} ${shadow} ${width} font-semibold transition-all duration-300 transform hover:scale-105 inline-block text-center`;
        previewBtnLive.textContent = buttonText;
    }
}

const form = document.getElementById('hero-form');
if (form) {
    form.querySelectorAll('input, select, textarea').forEach(el => {
        el.addEventListener('input', updatePreview);
        el.addEventListener('change', updatePreview);
    });
}

const titleColorInput = document.querySelector('#id_title_color');
if (titleColorInput) titleColorInput.addEventListener('input', updateTitlePreview);

const subtitleColorInput = document.querySelector('#id_subtitle_color');
if (subtitleColorInput) subtitleColorInput.addEventListener('input', updateSubtitlePreview);

const previewBgColor = document.getElementById('preview-bg-color');
if (previewBgColor) {
    previewBgColor.addEventListener('input', function() {
        document.getElementById('preview-bg-color-value').textContent = this.value;
        updateTitlePreview();
        updateSubtitlePreview();
    });
}

document.querySelectorAll('input[name="content_alignment"]').forEach(radio => {
    radio.addEventListener('change', updatePreview);
});

document.addEventListener('DOMContentLoaded', function() {
    updatePreview();
    updateButtonPreview();
    updateOverlayPreview();
    updateTitlePreview();
    updateSubtitlePreview();
});