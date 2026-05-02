// ============================================
// DATOS GLOBALES
// ============================================
const zicadaData = globalThis.zicadaData;
const variantsData = zicadaData.variants;
const galleryImages = zicadaData.gallery;
const config = zicadaData.config;

// URLs para las peticiones AJAX
const CART_ADD_URL = config.cartAddUrl;
const CSRF_TOKEN = config.csrfToken;
const PLACEHOLDER_IMAGE = config.staticPlaceholder;

// ============================================
// ESTADO DE LA PÁGINA
// ============================================
let selectedColorId = null;
let selectedSizeId = null;
let currentVariant = null;

// ============================================
// FUNCIONES AUXILIARES
// ============================================
function getUniqueColors() {
    const unique = new Map();
    variantsData.forEach(v => {
        if (!unique.has(v.color_id)) {
            unique.set(v.color_id, {
                id: v.color_id,
                name: v.color_name,
                code: v.color_code
            });
        }
    });
    return Array.from(unique.values());
}

function getUniqueSizes() {
    const unique = new Map();
    variantsData.forEach(v => {
        if (!unique.has(v.size_id)) {
            unique.set(v.size_id, {
                id: v.size_id,
                name: v.size_name
            });
        }
    });
    return Array.from(unique.values());
}

function getVariantByColorAndSize(colorId, sizeId) {
    if (colorId && sizeId) {
        return variantsData.find(v => v.color_id === colorId && v.size_id === sizeId);
    }
    return null;
}

function isVariantAvailable(colorId, sizeId) {
    const variant = getVariantByColorAndSize(colorId, sizeId);
    return variant && variant.stock > 0;
}

// ============================================
// FUNCIONES AUXILIARES DE ACTUALIZACIÓN UI
// ============================================
function updateProductPrice() {
    const priceElement = document.getElementById('product-price');
    if (currentVariant) {
        priceElement.innerText = `$${currentVariant.price.toLocaleString()}`;
    }
}

function updateStockInfo() {
    const stockInfo = document.getElementById('stock-info');
    const addBtn = document.getElementById('add-to-cart-btn');
    
    if (!currentVariant) {
        stockInfo.innerHTML = '<span class="text-gray-500">Selecciona un color y una talla</span>';
        addBtn.disabled = true;
        return;
    }
    
    if (currentVariant.stock === 0) {
        stockInfo.innerHTML = '<span class="text-red-600">Agotado</span>';
        addBtn.disabled = true;
    } else if (currentVariant.stock <= 10) {
        stockInfo.innerHTML = `<span class="text-red-500">¡Últimas ${currentVariant.stock} unidades!</span>`;
        addBtn.disabled = false;
    } else {
        stockInfo.innerHTML = '<span class="text-green-600">Disponible</span>';
        addBtn.disabled = false;
    }
}

function updateQuantityInput() {
    const quantityInput = document.getElementById('quantity');
    if (!currentVariant) return;
    
    const maxStock = currentVariant.stock > 0 ? currentVariant.stock : 1;
    quantityInput.max = maxStock;
    
    const currentValue = Number.parseInt(quantityInput.value);
    if (currentValue > maxStock && maxStock > 0) {
        quantityInput.value = maxStock;
    }
}

function updateMainImage() {
    const mainImage = document.getElementById('main-image');
    if (currentVariant?.image && currentVariant.image !== '') {
        mainImage.src = currentVariant.image;
    }
}

function updateSizeSelectorState() {
    const container = document.getElementById('size-selector');
    if (!container) return;
    
    container.querySelectorAll('.variant-btn').forEach(btn => {
        const sizeId = Number.parseInt(btn.dataset.id);
        if (selectedColorId && !isVariantAvailable(selectedColorId, sizeId)) {
            btn.classList.add('disabled');
        } else {
            btn.classList.remove('disabled');
        }
    });
}

function updateColorSelectorState() {
    const container = document.getElementById('color-selector');
    if (!container) return;
    
    container.querySelectorAll('.variant-btn').forEach(btn => {
        const colorId = Number.parseInt(btn.dataset.id);
        if (selectedSizeId && !isVariantAvailable(colorId, selectedSizeId)) {
            btn.classList.add('disabled');
        } else {
            btn.classList.remove('disabled');
        }
    });
}

function checkStockWarning() {
    const quantityInput = document.getElementById('quantity');
    const warning = document.getElementById('stock-warning');
    const addBtn = document.getElementById('add-to-cart-btn');
    
    if (!warning || !addBtn || !quantityInput) return;
    
    const quantity = Number.parseInt(quantityInput.value, 10);
    
    if (currentVariant && quantity > currentVariant.stock && currentVariant.stock > 0) {
        warning.classList.remove('hidden');
        addBtn.disabled = true;
    } else {
        warning.classList.add('hidden');
        if (currentVariant && currentVariant.stock > 0) {
            addBtn.disabled = false;
        }
    }
}

// ============================================
// FUNCIÓN PRINCIPAL UPDATE UI
// ============================================
function updateUI() {
    if (selectedColorId && selectedSizeId) {
        currentVariant = getVariantByColorAndSize(selectedColorId, selectedSizeId);
    } else {
        currentVariant = null;
    }
    
    updateProductPrice();
    updateStockInfo();
    updateQuantityInput();
    updateMainImage();
    updateSizeSelectorState();
    updateColorSelectorState();
    checkStockWarning();
}

// ============================================
// RENDERIZADO DE SELECTORES
// ============================================
function renderColorSelector() {
    const container = document.getElementById('color-selector');
    const colors = getUniqueColors();
    
    container.innerHTML = colors.map(color => `
        <div class="variant-btn flex items-center gap-2 border rounded-lg px-4 py-2 transition"
            data-id="${color.id}"
            data-name="${color.name}">
            <div class="color-preview" style="background-color: ${color.code};"></div>
            <span>${color.name}</span>
        </div>
    `).join('');
    
    container.querySelectorAll('.variant-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.classList.contains('disabled')) return;
            
            selectedColorId = Number.parseInt(btn.dataset.id, 10);
            container.querySelectorAll('.variant-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            
            const firstImage = galleryImages.find(img => img?.color_id === selectedColorId);
            const mainImage = document.getElementById('main-image');
            mainImage.src = firstImage?.image || PLACEHOLDER_IMAGE;
            
            updateGalleryByColor(selectedColorId);
            updateUI();
        });
    });
}

function renderSizeSelector() {
    const container = document.getElementById('size-selector');
    const sizes = getUniqueSizes();
    
    container.innerHTML = sizes.map(size => `
        <div class="variant-btn border rounded-lg px-5 py-2 text-center transition"
             data-id="${size.id}">
            ${size.name}
        </div>
    `).join('');
    
    container.querySelectorAll('.variant-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.classList.contains('disabled')) return;
            selectedSizeId = Number.parseInt(btn.dataset.id);
            container.querySelectorAll('.variant-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            updateUI();
        });
    });
}

// ============================================
// GALERÍA
// ============================================
function updateGalleryByColor(colorId) {
    const galleryContainer = document.getElementById('thumbnail-gallery');
    if (!galleryContainer) return;
    
    if (!galleryImages || galleryImages.length === 0) {
        galleryContainer.innerHTML = '<div class="text-center text-gray-500 col-span-4">No hay imágenes disponibles</div>';
        return;
    }
    
    let filteredImages = galleryImages;
    if (colorId) {
        filteredImages = galleryImages.filter(img => img && img.color_id == colorId);
    }
    
    if (!filteredImages || filteredImages.length === 0) {
        galleryContainer.innerHTML = '<div class="text-center text-gray-500 col-span-4">No hay imágenes para este color</div>';
        return;
    }
    
    galleryContainer.innerHTML = filteredImages.map(img => `
        <div class="product-gallery-thumb rounded-lg overflow-hidden bg-gray-100" 
             data-image="${img.image || ''}"
             data-color-id="${img.color_id || ''}"
             data-color-name="${img.color_name || ''}"
             onclick="window.changeMainImage('${img.image || ''}', ${img.color_id || 0}, event)">
            <img src="${img.image || ''}" alt="${img.color_name || ''}" class="w-full h-24 object-cover">
            <div class="text-center text-xs py-1">${img.color_name || ''}</div>
        </div>
    `).join('');
}

globalThis.changeMainImage = function(imageUrl, colorId, event) {
    const mainImage = document.getElementById('main-image');
    if (imageUrl && imageUrl !== '') {
        mainImage.src = imageUrl;
    }
    
    document.querySelectorAll('.product-gallery-thumb').forEach(thumb => {
        thumb.classList.remove('active');
    });
    
    const thumb = event?.target?.closest?.('.product-gallery-thumb');
    if (thumb) thumb.classList.add('active');
    
    if (colorId && colorId !== selectedColorId) {
        const colorBtn = document.querySelector(`#color-selector .variant-btn[data-id="${colorId}"]`);
        if (colorBtn && !colorBtn.classList.contains('disabled')) {
            colorBtn.click();
        }
    }
};

// ============================================
// DOM CACHE
// ============================================
const DOM = {
    get decreaseBtn() { return document.getElementById('decrease-qty'); },
    get increaseBtn() { return document.getElementById('increase-qty'); },
    get quantityInput() { return document.getElementById('quantity'); },
    get addBtn() { return document.getElementById('add-to-cart-btn'); },
    get clearBtn() { return document.getElementById('clear-selection-btn'); },
    get cartCountSpan() { return document.getElementById('cart-count'); }
};

// ============================================
// QUANTITY BUTTONS
// ============================================
function setupQuantityButtons() {
    const { decreaseBtn, increaseBtn, quantityInput } = DOM;
    
    if (decreaseBtn) {
        decreaseBtn.addEventListener('click', () => {
            let val = Number.parseInt(quantityInput.value, 10);
            if (val > 1) {
                quantityInput.value = val - 1;
                checkStockWarning();
            }
        });
    }
    
    if (increaseBtn) {
        increaseBtn.addEventListener('click', () => {
            let val = Number.parseInt(quantityInput.value, 10);
            let max = currentVariant?.stock || 99;
            if (val < max) {
                quantityInput.value = val + 1;
                checkStockWarning();
            } else if (max > 0 && val !== max) {
                quantityInput.value = max;
                checkStockWarning();
            }
        });
    }
    
    if (quantityInput) {
        quantityInput.addEventListener('change', () => {
            let val = Number.parseInt(quantityInput.value, 10);
            let max = currentVariant?.stock || 99;
            if (Number.isNaN(val)) val = 1;
            if (val < 1) val = 1;
            if (val > max && max > 0) val = max;
            quantityInput.value = val;
            checkStockWarning();
        });
    }
}

// ============================================
// ADD TO CART
// ============================================
let isAddingToCart = false;

function setupAddToCart() {
    const { addBtn } = DOM;
    if (!addBtn || addBtn._hasListener) return;
    
    addBtn._hasListener = true;
    addBtn.addEventListener('click', handleAddToCart);
}

async function handleAddToCart() {
    if (isAddingToCart) return;
    
    const quantity = Number.parseInt(DOM.quantityInput?.value || 1, 10);
    
    if (!selectedColorId || !selectedSizeId || !currentVariant || quantity > currentVariant.stock) {
        location.reload();
        return;
    }
    
    isAddingToCart = true;
    const { addBtn, cartCountSpan } = DOM;
    
    if (addBtn) {
        addBtn.disabled = true;
        addBtn.textContent = 'Agregando...';
    }
    
    try {
        const response = await fetch(CART_ADD_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({
                variant_id: currentVariant.id,
                quantity: quantity
            })
        });
        
        const data = await response.json();
        
        if (data.success && cartCountSpan) {
            cartCountSpan.textContent = data.total_items;
        }
        
        location.reload();
    } catch (error) {
        console.error('Error:', error);
        location.reload();
    } finally {
        isAddingToCart = false;
    }
}

// ============================================
// CLEAR SELECTION
// ============================================
function setupClearSelection() {
    const { clearBtn } = DOM;
    if (!clearBtn) return;
    
    clearBtn.addEventListener('click', () => {
        selectedColorId = null;
        selectedSizeId = null;
        currentVariant = null;
        
        document.querySelectorAll('#color-selector .variant-btn, #size-selector .variant-btn')
            .forEach(btn => btn.classList.remove('selected'));
        
        if (DOM.quantityInput) DOM.quantityInput.value = 1;
        
        updateGalleryByColor(null);
        updateUI();
        
        const mainImage = document.getElementById('main-image');
        const firstImage = galleryImages?.[0]?.image;
        if (mainImage) mainImage.src = firstImage || PLACEHOLDER_IMAGE;
    });
}

// ============================================
// INICIALIZACIÓN
// ============================================
function init() {
    renderColorSelector();
    renderSizeSelector();
    setupQuantityButtons();
    updateGalleryByColor(null);
    setupAddToCart();
    setupClearSelection();
    updateUI();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}