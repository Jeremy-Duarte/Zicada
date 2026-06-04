(function(global) {
    'use strict';

    class CloudinarySingleImageWidget {
        constructor(widgetElement) {
            if (!widgetElement) return;
            this.widget = widgetElement;
            this.fileInput = widgetElement.querySelector('input[type="file"]');
            this.previewContainer = widgetElement.querySelector('.single-image-preview');
            this.init();
        }

        init() {
            if (!this.fileInput) return;
            this.attachEvents();
        }

        attachEvents() {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
            
            const clearCheckbox = this.widget.querySelector('input[type="checkbox"][name*="-clear"]');
            if (clearCheckbox) {
                clearCheckbox.addEventListener('change', (e) => this.handleClear(e));
            }
        }

        handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.showPreview(e.target.result);
                };
                reader.readAsDataURL(file);
            }
        }

        handleClear(event) {
            if (event.target.checked) {
                this.clearPreview();
            }
        }

        showPreview(imageUrl) {
            if (!this.previewContainer) return;
            
            this.previewContainer.innerHTML = `
                <div class="mt-3 relative inline-block">
                    <img src="${imageUrl}" class="w-32 h-32 object-cover rounded-lg shadow-md border-2 border-green-500">
                    <span class="absolute -top-2 -right-2 bg-green-500 text-white text-xs rounded-full px-1.5 py-0.5">
                        <i class="fas fa-check"></i>
                    </span>
                    <button type="button" class="absolute -bottom-2 left-1/2 transform -translate-x-1/2 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full hover:bg-red-600 remove-preview-btn">
                        <i class="fas fa-times"></i> Eliminar
                    </button>
                </div>
                <p class="text-xs text-gray-500 mt-2">Imagen seleccionada</p>
            `;
            
            const removeBtn = this.previewContainer.querySelector('.remove-preview-btn');
            if (removeBtn) {
                removeBtn.addEventListener('click', () => {
                    this.fileInput.value = '';
                    this.clearPreview();
                    const clearCheckbox = this.widget.querySelector('input[type="checkbox"][name*="-clear"]');
                    if (clearCheckbox) clearCheckbox.checked = true;
                });
            }
        }

        clearPreview() {
            if (this.previewContainer) {
                this.previewContainer.innerHTML = `
                    <div class="mt-3 text-center text-gray-400">
                        <i class="fas fa-image text-3xl mb-1 block"></i>
                        <p class="text-xs">Sin imagen seleccionada</p>
                    </div>
                `;
            }
        }
    }

    function initWidgets() {
        const widgets = document.querySelectorAll('.cloudinary-single-image-widget');
        widgets.forEach(widget => {
            if (widget.dataset.initialized === 'true') return;
            widget.dataset.initialized = 'true';
            try {
                new CloudinarySingleImageWidget(widget);
            } catch (error) {
                console.error('Error initializing Cloudinary single image widget:', error);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWidgets);
    } else {
        initWidgets();
    }

    const observer = new MutationObserver(() => initWidgets());
    observer.observe(document.body, { childList: true, subtree: true });

    globalThis.CloudinarySingleImageWidget = CloudinarySingleImageWidget;
})(globalThis);