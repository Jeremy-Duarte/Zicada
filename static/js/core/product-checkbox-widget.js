(function(global) {
    'use strict';

    class ProductCheckboxWidget {
        constructor(widgetElement) {
            if (!widgetElement) return;
            this.widget = widgetElement;
            this.hiddenSelect = widgetElement.querySelector('select');
            this.checkboxes = widgetElement.querySelectorAll('.product-item input[type="checkbox"]');
            this.searchInput = widgetElement.querySelector('.product-search');
            this.productGrid = widgetElement.querySelector('.grid');
            this.searchTimer = null;
            this.init();
        }

        init() {
            if (!this.hiddenSelect || !this.checkboxes.length) return;
            this.syncFromSelectToCheckboxes();
            this.attachEvents();
            this.attachSearchEvents();
        }

        syncFromSelectToCheckboxes() {
            const selectedValues = new Set(
                Array.from(this.hiddenSelect.options)
                    .filter(opt => opt.selected)
                    .map(opt => opt.value)
            );
            
            this.checkboxes.forEach(cb => {
                cb.checked = selectedValues.has(cb.value);
                this.updateCheckboxStyle(cb);
            });
        }

        updateCheckboxStyle(checkbox) {
            const parentLabel = checkbox.closest('.product-item');
            if (!parentLabel) return;
            
            const imageDiv = parentLabel.querySelector('div:first-of-type');
            const indicatorDiv = parentLabel.querySelector('.absolute.top-1.right-1 div');
            
            if (checkbox.checked) {
                imageDiv?.classList.remove('border-gray-200');
                imageDiv?.classList.add('border-zicada-accent', 'ring-2', 'ring-zicada-accent/30');
                if (indicatorDiv) {
                    indicatorDiv.classList.remove('bg-gray-300');
                    indicatorDiv.classList.add('bg-zicada-accent');
                }
            } else {
                imageDiv?.classList.remove('border-zicada-accent', 'ring-2', 'ring-zicada-accent/30');
                imageDiv?.classList.add('border-gray-200');
                if (indicatorDiv) {
                    indicatorDiv.classList.remove('bg-zicada-accent');
                    indicatorDiv.classList.add('bg-gray-300');
                }
            }
        }

        attachEvents() {
            // Solo el evento 'change' de los checkboxes (sin listener de click redundante)
            this.checkboxes.forEach(cb => {
                cb.addEventListener('change', () => {
                    this.updateCheckboxStyle(cb);
                    this.updateHiddenSelect();
                });
            });
        }

        attachSearchEvents() {
            if (!this.searchInput) return;
            
            this.searchInput.addEventListener('input', (e) => {
                const term = e.target.value.toLowerCase().trim();
                
                if (this.searchTimer) {
                    clearTimeout(this.searchTimer);
                }
                
                this.searchTimer = setTimeout(() => {
                    this.filterProducts(term);
                }, 300);
            });
        }

        filterProducts(term) {
            const productItems = this.widget.querySelectorAll('.product-item');
            let hasResults = false;
            
            const isSearchValid = term.length >= 2;
            
            if (isSearchValid) {
                productItems.forEach(item => {
                    const name = item.querySelector('.font-medium')?.textContent.toLowerCase() || '';
                    const category = item.querySelector('.text-gray-500')?.textContent.toLowerCase() || '';
                    
                    if (name.includes(term) || category.includes(term)) {
                        item.style.display = '';
                        hasResults = true;
                    } else {
                        item.style.display = 'none';
                    }
                });
                
                if (hasResults) {
                    this.hideNoResults();
                } else {
                    this.showNoResults();
                }
            } else {
                productItems.forEach(item => {
                    item.style.display = '';
                });
                this.hideNoResults();
            }
        }


        showNoResults() {
            let noResultsMsg = this.widget.querySelector('.no-results-msg');
            if (!noResultsMsg) {
                noResultsMsg = document.createElement('div');
                noResultsMsg.className = 'no-results-msg col-span-full text-center py-8';
                noResultsMsg.innerHTML = `
                    <i class="fas fa-search text-3xl mb-2 block text-gray-400"></i>
                    <p class="text-gray-400 text-sm">No se encontraron productos que coincidan con tu búsqueda.</p>
                `;
                this.productGrid.appendChild(noResultsMsg);
            }
            noResultsMsg.style.display = '';
        }

        hideNoResults() {
            const noResultsMsg = this.widget.querySelector('.no-results-msg');
            if (noResultsMsg) {
                noResultsMsg.style.display = 'none';
            }
        }

        updateHiddenSelect() {
            const selectedValuesSet = new Set(
                Array.from(this.checkboxes)
                    .filter(cb => cb.checked)
                    .map(cb => cb.value)
            );
            
            let changed = false;
            
            Array.from(this.hiddenSelect.options).forEach(opt => {
                const shouldBeSelected = selectedValuesSet.has(opt.value);
                if (opt.selected !== shouldBeSelected) {
                    opt.selected = shouldBeSelected;
                    changed = true;
                }
            });
            
            if (changed) {
                this.hiddenSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    }

    function initWidgets() {
        const widgets = document.querySelectorAll('.product-select-widget');
        widgets.forEach(widget => {
            if (widget.dataset.initialized === 'true') return;
            widget.dataset.initialized = 'true';
            try {
                new ProductCheckboxWidget(widget);
            } catch (error) {
                console.error('Error initializing product checkbox widget:', error);
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

    globalThis.ProductCheckboxWidget = ProductCheckboxWidget;
})(globalThis);