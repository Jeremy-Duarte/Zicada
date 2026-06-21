// ============================================================
// FILTER SIDEBAR - Alpine.js Component
// ============================================================

document.addEventListener('alpine:init', () => {
    Alpine.data('filterSidebar', () => ({
        // ============================================================
        // ESTADO - Inicializado desde data attributes
        // ============================================================
        mobileOpen: false,
        
        // Filtros (se inicializan desde data attributes)
        searchQuery: '',
        currentCategory: '',
        currentProductType: '',
        currentStatus: '',
        currentDateFilter: '',
        currentOrderBy: '',
        
        // Precio
        minGlobal: 0,
        maxGlobal: 1000000,
        minPrice: 0,
        maxPrice: 1000000,
        
        // Product Count
        productCountMin: '',
        productCountMax: '',
        
        // ============================================================
        // COMPUTED
        // ============================================================
        get activeFilterCount() {
            let count = 0;
            if (this.searchQuery && this.searchQuery.trim() !== '') count++;
            if (this.currentCategory) count++;
            if (this.currentProductType) count++;
            if (this.minPrice > this.minGlobal || this.maxPrice < this.maxGlobal) count++;
            if (this.currentStatus) count++;
            if (this.currentDateFilter) count++;
            if (this.currentOrderBy && this.currentOrderBy !== '-created_at') count++;
            if (this.productCountMin || this.productCountMax) count++;
            return count;
        },
        
        get hasPriceFilter() {
            return this.minPrice > this.minGlobal || this.maxPrice < this.maxGlobal;
        },
        
        // ============================================================
        // MÉTODOS
        // ============================================================
        init() {
            // Inicializar desde data attributes
            this.$watch('searchQuery', () => {});
            
            // Cerrar móvil en resize a desktop
            window.addEventListener('resize', () => {
                if (window.innerWidth >= 1024) {
                    this.mobileOpen = false;
                }
            });
        },
        
        setFilter(key, value) {
            if (key === 'category') this.currentCategory = value;
            else if (key === 'product_type') this.currentProductType = value;
            else if (key === 'status') this.currentStatus = value;
            else if (key === 'date_filter') this.currentDateFilter = value;
            else if (key === 'order_by') this.currentOrderBy = value;
            this.submitForm();
        },
        
        submitForm() {
            const form = document.getElementById('filter-form');
            if (form) {
                form.requestSubmit();
            }
        },
        
        updatePrice() {
            clearTimeout(this._priceTimeout);
            this._priceTimeout = setTimeout(() => {
                this.submitForm();
            }, 400);
        },
        
        resetPrice() {
            this.minPrice = this.minGlobal;
            this.maxPrice = this.maxGlobal;
            this.submitForm();
        },
        
        removeFilter(filterName) {
            if (filterName === 'search') {
                this.searchQuery = '';
                const searchInput = document.getElementById('filter-search');
                if (searchInput) searchInput.value = '';
            } else if (filterName === 'category') {
                this.currentCategory = '';
            } else if (filterName === 'product_type') {
                this.currentProductType = '';
            } else if (filterName === 'status') {
                this.currentStatus = '';
            } else if (filterName === 'date_filter') {
                this.currentDateFilter = '';
            } else if (filterName === 'order_by') {
                this.currentOrderBy = '-created_at';
            } else if (filterName === 'price') {
                this.minPrice = this.minGlobal;
                this.maxPrice = this.maxGlobal;
            } else if (filterName === 'product_count') {
                this.productCountMin = '';
                this.productCountMax = '';
                const minInput = document.getElementById('product-count-min');
                const maxInput = document.getElementById('product-count-max');
                if (minInput) minInput.value = '';
                if (maxInput) maxInput.value = '';
            }
            this.submitForm();
        },
        
        clearAllFilters() {
            // 1. Limpiar estado de Alpine
            this.searchQuery = '';
            this.currentCategory = '';
            this.currentProductType = '';
            this.currentStatus = '';
            this.currentDateFilter = '';
            this.currentOrderBy = '-created_at';
            this.minPrice = this.minGlobal;
            this.maxPrice = this.maxGlobal;
            this.productCountMin = '';
            this.productCountMax = '';
            
            // 2. Limpiar inputs visuales
            const searchInput = document.getElementById('filter-search');
            if (searchInput) searchInput.value = '';
            
            const minInput = document.getElementById('product-count-min');
            const maxInput = document.getElementById('product-count-max');
            if (minInput) minInput.value = '';
            if (maxInput) maxInput.value = '';
            
            // 3. Limpiar los inputs ocultos del formulario
            const form = document.getElementById('filter-form');
            if (form) {
                const hiddenInputs = form.querySelectorAll('input[type="hidden"]');
                hiddenInputs.forEach(input => {
                    input.value = '';
                });
                
                // 4. Actualizar hx-get a la URL limpia (sin parámetros)
                const cleanUrl = form.dataset.cleanUrl || window.location.pathname;
                form.setAttribute('hx-get', cleanUrl);
                
                // 5. Enviar el formulario
                form.requestSubmit();
            }
        },
        
        // ============================================================
        // HELPERS
        // ============================================================
        formatPrice(value) {
            return new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'COP',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(value);
        },
        
        productTypeLabel(type) {
            // Se pasa desde el template via data attribute
            const labels = this.$el.dataset.productTypeLabels ? 
                JSON.parse(this.$el.dataset.productTypeLabels) : {};
            return labels[type] || type;
        },
        
        orderLabel(value) {
            // Se pasa desde el template via data attribute
            const choices = this.$el.dataset.orderChoices ? 
                JSON.parse(this.$el.dataset.orderChoices) : [];
            for (let choice of choices) {
                if (choice[0] === value) return choice[1];
            }
            return value;
        }
    }));
});

// ============================================================
// HTMX - Sincronizar Alpine después del swap
// ============================================================
document.addEventListener('htmx:afterSwap', function(event) {
    const sidebar = document.querySelector('.filter-sidebar');
    if (sidebar && sidebar._x_dataStack) {
        const data = Alpine.$data(sidebar);
        if (data) {
            const form = document.getElementById('filter-form');
            if (form) {
                const minPriceInput = form.querySelector('input[name="min_price"]');
                const maxPriceInput = form.querySelector('input[name="max_price"]');
                const searchInput = document.getElementById('filter-search');
                const categoryInput = form.querySelector('input[name="category"]');
                const productTypeInput = form.querySelector('input[name="product_type"]');
                const statusInput = form.querySelector('input[name="status"]');
                const dateFilterInput = form.querySelector('input[name="date_filter"]');
                const orderByInput = form.querySelector('input[name="order_by"]');
                const countMinInput = form.querySelector('input[name="product_count_min"]');
                const countMaxInput = form.querySelector('input[name="product_count_max"]');
                
                if (minPriceInput) data.minPrice = parseInt(minPriceInput.value) || data.minGlobal;
                if (maxPriceInput) data.maxPrice = parseInt(maxPriceInput.value) || data.maxGlobal;
                if (searchInput) data.searchQuery = searchInput.value;
                if (categoryInput) data.currentCategory = categoryInput.value;
                if (productTypeInput) data.currentProductType = productTypeInput.value;
                if (statusInput) data.currentStatus = statusInput.value;
                if (dateFilterInput) data.currentDateFilter = dateFilterInput.value;
                if (orderByInput) data.currentOrderBy = orderByInput.value;
                if (countMinInput) data.productCountMin = countMinInput.value;
                if (countMaxInput) data.productCountMax = countMaxInput.value;
            }
        }
    }
});