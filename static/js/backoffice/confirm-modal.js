(function() {
    'use strict';
    
    // DOM Elements cache
    let modal = null;
    let modalForm = null;
    let modalBulkAction = null;
    let modalTitle = null;
    let modalMessage = null;
    let modalDetail = null;
    let modalIcon = null;
    let modalCancel = null;
    let modalConfirm = null;
    let pendingExtraData = null;
    
    // Configuración de tipos de modales
    const MODAL_TYPES = {
        warning: {
            icon: 'fa-exclamation-triangle',
            bgClass: 'bg-amber-100',
            colorClass: 'text-amber-600',
            confirmClass: 'bg-zicada-accent hover:bg-red-700',
            confirmText: 'Confirmar'
        },
        danger: {
            icon: 'fa-trash-alt',
            bgClass: 'bg-red-100',
            colorClass: 'text-red-600',
            confirmClass: 'bg-red-600 hover:bg-red-700',
            confirmText: 'Eliminar'
        },
        success: {
            icon: 'fa-check-circle',
            bgClass: 'bg-green-100',
            colorClass: 'text-green-600',
            confirmClass: 'bg-green-600 hover:bg-green-700',
            confirmText: 'Confirmar'
        },
        info: {
            icon: 'fa-info-circle',
            bgClass: 'bg-blue-100',
            colorClass: 'text-blue-600',
            confirmClass: 'bg-blue-600 hover:bg-blue-700',
            confirmText: 'Confirmar'
        }
    };
    
    function initModal() {
        modal = document.getElementById('confirm-modal');
        if (!modal) return;
        
        modalForm = document.getElementById('confirm-form');
        modalBulkAction = document.getElementById('modal-bulk-action');
        modalTitle = document.getElementById('modal-title');
        modalMessage = document.getElementById('modal-message');
        modalDetail = document.getElementById('modal-detail');
        modalIcon = document.getElementById('modal-icon');
        modalCancel = document.getElementById('modal-cancel');
        modalConfirm = document.getElementById('modal-confirm');
        
        modalCancel?.addEventListener('click', closeModal);
        modalForm?.addEventListener('submit', handleFormSubmit);
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
        
        globalThis.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal?.classList?.contains('flex')) {
                closeModal();
            }
        });
    }
    
    function handleFormSubmit() {
        if (pendingExtraData && Object.keys(pendingExtraData).length > 0) {
            Object.entries(pendingExtraData).forEach(([name, value]) => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = name;
                input.value = value;
                modalForm?.appendChild(input);
            });
            pendingExtraData = null;
        }
    }
    
    function closeModal() {
        if (!modal) return;
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        if (modalBulkAction) modalBulkAction.value = '';
        pendingExtraData = null;
    }
    
    function getModalTypeConfig(type) {
        return MODAL_TYPES[type] || MODAL_TYPES.warning;
    }
    
    function updateModalUI(options) {
        const {
            title = 'Confirmar acción',
            message = '¿Estás seguro?',
            detail = '',
            type = 'warning',
            action = '',
            extraData = {}
        } = options;
        
        const typeConfig = getModalTypeConfig(type);
        
        if (modalIcon) {
            modalIcon.innerHTML = `<i class="fas ${typeConfig.icon} ${typeConfig.colorClass}"></i>`;
            modalIcon.className = `w-10 h-10 rounded-full ${typeConfig.bgClass} flex items-center justify-center`;
        }
        if (modalTitle) modalTitle.textContent = title;
        if (modalMessage) modalMessage.textContent = message;
        if (modalDetail) modalDetail.textContent = detail;
        if (modalConfirm) {
            modalConfirm.className = `flex-1 px-4 py-2 rounded-lg text-white transition ${typeConfig.confirmClass}`;
            modalConfirm.textContent = typeConfig.confirmText;
        }
        if (modalBulkAction) modalBulkAction.value = action;
        
        pendingExtraData = extraData;
    }
    
    function openModal() {
        if (!modal) return;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
    
    globalThis.ConfirmModal = {
        show(options) {
            initModal();
            if (!modal) return;
            updateModalUI(options);
            openModal();
        },
        close: closeModal
    };
    
    // Auto-inicializar
    const isReady = document.readyState !== 'loading';
    if (isReady) {
        initModal();
    } else {
        document.addEventListener('DOMContentLoaded', initModal);
    }
})();