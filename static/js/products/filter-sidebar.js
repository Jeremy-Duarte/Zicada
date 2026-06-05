(function() {
    const TOGGLE_BTN_ID = 'toggle-filters-btn';
    const FILTERS_CONTENT_ID = 'filters-content';
    const STORAGE_HIDDEN_KEY = 'filters_hidden';

    function initMobileFiltersToggle() {
        const toggleBtn = document.getElementById(TOGGLE_BTN_ID);
        const filtersContent = document.getElementById(FILTERS_CONTENT_ID);
        
        if (!toggleBtn || !filtersContent) return;
        
        const isHidden = localStorage.getItem(STORAGE_HIDDEN_KEY) === 'true';
        if (isHidden && window.innerWidth < 1024) {
            filtersContent.classList.add('hidden');
        }
        
        toggleBtn.addEventListener('click', function() {
            filtersContent.classList.toggle('hidden');
            const nowHidden = filtersContent.classList.contains('hidden');
            localStorage.setItem(STORAGE_HIDDEN_KEY, nowHidden);
            updateArrowRotation(toggleBtn, nowHidden);
        });
        
        const initialHidden = filtersContent.classList.contains('hidden');
        updateArrowRotation(toggleBtn, initialHidden);
    }

    function updateArrowRotation(toggleBtn, isHidden) {
        const arrow = toggleBtn.querySelector('svg:last-child');
        if (arrow) {
            arrow.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(180deg)';
        }
    }

    function getStorageKey(form) {
        return form.dataset.persistKey || 'filter_values';
    }

    function loadSavedFilters(form) {
        const storageKey = getStorageKey(form);
        const savedValues = localStorage.getItem(storageKey);
        if (!savedValues) return;
        
        try {
            const values = JSON.parse(savedValues);
            for (const [name, value] of Object.entries(values)) {
                const input = form.querySelector(`[name="${name}"]`);
                if (input && value) {
                    input.value = value;
                }
            }
        } catch (error) {
            console.warn('Error loading saved filters:', error);
            localStorage.removeItem(storageKey);
        }
    }

    function saveCurrentFilters(form) {
        const storageKey = getStorageKey(form);
        const formData = new FormData(form);
        const values = {};
        for (const [key, value] of formData.entries()) {
            if (value && value !== '') {
                values[key] = value;
            }
        }
        localStorage.setItem(storageKey, JSON.stringify(values));
    }

    function clearSavedFilters(form) {
        const storageKey = getStorageKey(form);
        localStorage.removeItem(storageKey);
    }

    function attachFilterEvents(form) {
        const inputs = form.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                saveCurrentFilters(form);
            });
        });
        
        form.addEventListener('submit', function() {
            saveCurrentFilters(form);
        });
    }

    function attachClearButtons(form) {
        const clearButtons = document.querySelectorAll('.clear-filters-btn, a[href*="?"], a[href*="clean"]');
        clearButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                if (btn.getAttribute('href') === form.action || btn.textContent.includes('Limpiar')) {
                    clearSavedFilters(form);
                }
            });
        });
        
        const cleanUrlLink = document.querySelector('a[href="' + form.action + '"]');
        if (cleanUrlLink) {
            cleanUrlLink.addEventListener('click', function() {
                clearSavedFilters(form);
            });
        }
    }

    function initFilterPersistence() {
        const form = document.getElementById('filter-form');
        if (!form) return;
        
        loadSavedFilters(form);
        attachFilterEvents(form);
        attachClearButtons(form);
    }

    document.addEventListener('DOMContentLoaded', function() {
        initMobileFiltersToggle();
        initFilterPersistence();
    });
})();