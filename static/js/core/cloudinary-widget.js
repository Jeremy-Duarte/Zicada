(function(global) {
    'use strict';

    /**
     * Gestiona la sincronización entre checkboxes y el select oculto
     * para el widget de selección de imágenes de Cloudinary.
     */
    class CloudinaryImageWidget {
        constructor(widgetElement) {
            if (!widgetElement) return;
            this.widget = widgetElement;
            this.hiddenSelect = widgetElement.querySelector('select');
            this.checkboxes = widgetElement.querySelectorAll('input[type="checkbox"]');
            this.init();
        }

        init() {
            if (!this.hiddenSelect || !this.checkboxes.length) return;
            this.syncFromSelectToCheckboxes();
            this.attachEvents();
        }

        // Sincroniza checkboxes según el select oculto (para valores iniciales)
        syncFromSelectToCheckboxes() {
            const selectedValues = Array.from(this.hiddenSelect.options)
                .filter(opt => opt.selected)
                .map(opt => opt.value);
            this.checkboxes.forEach(cb => {
                cb.checked = selectedValues.includes(cb.value);
                this.updateCheckboxStyle(cb);
            });
        }

        // Actualiza el estilo visual del checkbox (borde, marcador)
        updateCheckboxStyle(checkbox) {
            const parentLabel = checkbox.closest('label');
            if (!parentLabel) return;
            const imageDiv = parentLabel.querySelector('div:first-of-type');
            const indicatorDiv = parentLabel.querySelector('.absolute.top-1.right-1 div');
            if (checkbox.checked) {
                imageDiv?.classList.remove('border-gray-200');
                imageDiv?.classList.add('border-zicada-accent', 'ring-2', 'ring-zicada-accent/50');
                if (indicatorDiv) indicatorDiv.classList.remove('bg-gray-300');
                if (indicatorDiv) indicatorDiv.classList.add('bg-zicada-accent');
            } else {
                imageDiv?.classList.remove('border-zicada-accent', 'ring-2', 'ring-zicada-accent/50');
                imageDiv?.classList.add('border-gray-200');
                if (indicatorDiv) indicatorDiv.classList.remove('bg-zicada-accent');
                if (indicatorDiv) indicatorDiv.classList.add('bg-gray-300');
            }
        }

        attachEvents() {
            // Evento para cada checkbox
            this.checkboxes.forEach(cb => {
                cb.addEventListener('change', (e) => {
                    this.updateHiddenSelect();
                    this.updateCheckboxStyle(cb);
                });
            });
        }

        // Actualiza el select oculto según los checkboxes marcados
        updateHiddenSelect() {
            const selectedValues = Array.from(this.checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            // Actualizar las opciones del select
            Array.from(this.hiddenSelect.options).forEach(opt => {
                opt.selected = selectedValues.includes(opt.value);
            });
            // Disparar evento change para que Django capte el cambio
            this.hiddenSelect.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    // Inicializar todos los widgets al cargar la página
    function initWidgets() {
        const widgets = document.querySelectorAll('.cloudinary-image-widget');
        widgets.forEach(widget => {
            // Evitar doble inicialización
            if (widget.dataset.initialized === 'true') return;
            widget.dataset.initialized = 'true';
            try {
                new CloudinaryImageWidget(widget);
            } catch (error) {
                console.error('Error initializing Cloudinary image widget:', error);
            }
        });
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWidgets);
    } else {
        initWidgets();
    }

    // Soporte para formularios dinámicos (ej. formsets) usando MutationObserver
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1 && (node.matches?.('.cloudinary-image-widget') || node.querySelector?.('.cloudinary-image-widget'))) {
                    initWidgets();
                }
            });
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Exponer la clase globalmente si se necesita (opcional)
    global.CloudinaryImageWidget = CloudinaryImageWidget;
})(globalThis);