(function(global) {
    'use strict';

    class CloudinaryFeaturedWidget {
        constructor(widgetElement) {
            if (!widgetElement) return;
            this.widget = widgetElement;
            this.hiddenSelect = widgetElement.querySelector('select');
            this.gridContainer = widgetElement.querySelector('.featured-images-grid');
            this.imagesWidgetName = widgetElement.dataset.imagesWidgetName;
            this.imagesWidget = null;
            this.currentSelectedId = null;
            this.radioButtons = [];
            this.init();
        }

        init() {
            if (!this.hiddenSelect || !this.gridContainer) return;
            this.currentSelectedId = this.hiddenSelect.value;
            this.findImagesWidget();
            if (this.imagesWidget) {
                this.attachImageWidgetObserver();
                this.updateFromImagesWidget();
            }
        }

        findImagesWidget() {
            // Buscar por nombre o clase
            const allImageWidgets = document.querySelectorAll('.cloudinary-image-widget');
            for (const widget of allImageWidgets) {
                if (widget.dataset.widgetName === this.imagesWidgetName) {
                    this.imagesWidget = widget;
                    break;
                }
            }
            if (!this.imagesWidget && this.widget.closest('form')) {
                this.imagesWidget = this.widget.closest('form').querySelector('.cloudinary-image-widget');
            }
        }

        attachImageWidgetObserver() {
            if (!this.imagesWidget) return;
            
            // Observar cambios en los checkboxes del widget de imágenes
            const observer = new MutationObserver(() => this.updateFromImagesWidget());
            observer.observe(this.imagesWidget, { childList: true, subtree: true, attributes: true });
            
            // También escuchar eventos personalizados
            this.imagesWidget.addEventListener('images-changed', () => this.updateFromImagesWidget());
            
            // Escuchar directamente los checkboxes
            const checkboxes = this.imagesWidget.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(cb => {
                cb.addEventListener('change', () => this.updateFromImagesWidget());
            });
        }

        updateFromImagesWidget() {
            if (!this.imagesWidget) return;
            
            // Obtener las imágenes seleccionadas en el widget de imágenes
            const selectedImageIds = Array.from(this.imagesWidget.querySelectorAll('input[type="checkbox"]:checked'))
                .map(cb => cb.value);
            
            // Obtener los datos de las imágenes (URL, alt text)
            const selectedImages = [];
            selectedImageIds.forEach(imgId => {
                const imgElement = this.imagesWidget.querySelector(`input[type="checkbox"][value="${imgId}"]`);
                if (imgElement) {
                    const parentLabel = imgElement.closest('label');
                    const imgSrc = parentLabel?.querySelector('img')?.src || '';
                    const altText = parentLabel?.querySelector('img')?.alt || '';
                    selectedImages.push({ id: imgId, src: imgSrc, alt: altText });
                }
            });
            
            this.renderGrid(selectedImages);
        }

        renderGrid(images) {
            if (!this.gridContainer) return;
            
            if (images.length === 0) {
                this.gridContainer.innerHTML = `
                    <div class="col-span-full text-center py-8 text-gray-400">
                        <i class="fas fa-images text-3xl mb-2 block"></i>
                        <p>No hay imágenes seleccionadas.</p>
                        <p class="text-xs mt-1">Selecciona imágenes en el campo superior primero.</p>
                    </div>
                `;
                return;
            }
            
            const gridItems = [];
            const selectName = this.hiddenSelect.name;
            
            images.forEach(img => {
                const isSelected = this.currentSelectedId === img.id;
                gridItems.push(`
                    <label class="relative cursor-pointer group" data-image-id="${img.id}">
                        <input type="radio" name="${selectName}" value="${img.id}" ${isSelected ? 'checked' : ''}
                            class="absolute opacity-0 w-0 h-0 peer">
                        <div class="relative rounded-lg overflow-hidden border-2 transition-all 
                                    ${isSelected ? 'border-zicada-accent ring-2 ring-zicada-accent/50' : 'border-gray-200'}
                                    group-hover:border-zicada-accent group-hover:shadow-md">
                            <img src="${img.src}" alt="${img.alt || 'Imagen'}"
                                class="w-full h-24 object-cover">
                            <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 peer-checked:opacity-100 transition-opacity">
                                <i class="fas fa-check-circle text-white text-2xl drop-shadow-md"></i>
                            </div>
                        </div>
                        <div class="absolute top-1 right-1 w-5 h-5 rounded-full bg-white shadow-sm flex items-center justify-center">
                            <div class="w-4 h-4 rounded-full transition-colors ${isSelected ? 'bg-zicada-accent' : 'bg-gray-300'} peer-checked:bg-zicada-accent"></div>
                        </div>
                    </label>
                `);
            });
            
            const uploadUrl = '/products/admin/imagenes/subir/';
            gridItems.push(`
                <a href="${uploadUrl}" target="_blank"
                class="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg h-24
                        hover:border-zicada-accent transition group">
                    <i class="fas fa-plus text-gray-400 text-xl group-hover:text-zicada-accent"></i>
                    <span class="text-xs text-gray-400 mt-1">Subir</span>
                </a>
            `);
            
            this.gridContainer.innerHTML = gridItems.join('');
            this.attachRadioEvents();
        }

        attachRadioEvents() {
            const radios = this.gridContainer.querySelectorAll('input[type="radio"]');
            this.radioButtons = radios;
            
            radios.forEach(radio => {
                radio.removeEventListener('change', this.handleRadioChange);
                radio.addEventListener('change', this.handleRadioChange.bind(this));
            });
        }

        handleRadioChange(event) {
            const radio = event.target;
            if (radio.checked) {
                const newValue = radio.value;
                this.currentSelectedId = newValue;
                this.hiddenSelect.value = newValue;
                
                // Actualizar estilos visuales
                this.updateRadioStyles();
                
                // Disparar evento change
                this.hiddenSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }

        updateRadioStyles() {
            const allLabels = this.gridContainer.querySelectorAll('label');
            allLabels.forEach(label => {
                const radio = label.querySelector('input[type="radio"]');
                const imageDiv = label.querySelector('div:first-of-type');
                const indicatorDiv = label.querySelector('.absolute.top-1.right-1 div');
                
                if (radio && radio.checked) {
                    imageDiv?.classList.remove('border-gray-200');
                    imageDiv?.classList.add('border-zicada-accent', 'ring-2', 'ring-zicada-accent/50');
                    indicatorDiv?.classList.remove('bg-gray-300');
                    indicatorDiv?.classList.add('bg-zicada-accent');
                } else if (radio) {
                    imageDiv?.classList.remove('border-zicada-accent', 'ring-2', 'ring-zicada-accent/50');
                    imageDiv?.classList.add('border-gray-200');
                    indicatorDiv?.classList.remove('bg-zicada-accent');
                    indicatorDiv?.classList.add('bg-gray-300');
                }
            });
        }
    }

    function initWidgets() {
        const widgets = document.querySelectorAll('.cloudinary-featured-widget');
        widgets.forEach(widget => {
            if (widget.dataset.initializedFeatured === 'true') return;
            widget.dataset.initializedFeatured = 'true';
            try {
                new CloudinaryFeaturedWidget(widget);
            } catch (error) {
                console.error('Error initializing featured image widget:', error);
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

    globalThis.CloudinaryFeaturedWidget = CloudinaryFeaturedWidget;
})(globalThis);