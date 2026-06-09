(function() {
    'use strict';
    
    function initBulkActions() {
        const buttons = document.querySelectorAll('.bulk-action-btn');
        
        buttons.forEach(btn => {
            btn.removeEventListener('click', handleClick);
            btn.addEventListener('click', handleClick);
        });
    }
    
    function handleClick(event) {
        const button = event.currentTarget;
        const action = button.dataset.action;
        const confirmText = button.dataset.confirm || '¿Estás seguro?';
        const detailText = button.dataset.message || '';
        const type = button.dataset.type || 'warning';
        
        if (typeof ConfirmModal !== 'undefined') {
            ConfirmModal.show({
                title: 'Confirmar acción',
                message: confirmText,
                detail: detailText,
                type: type,
                action: action
            });
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initBulkActions);
    } else {
        initBulkActions();
    }
    
    document.addEventListener('turbo:load', initBulkActions);
    document.addEventListener('htmx:afterSwap', initBulkActions);
})();