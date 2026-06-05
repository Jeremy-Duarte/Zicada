document.addEventListener('DOMContentLoaded', function() {
    const menuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (menuButton && mobileMenu) {
        menuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    const searchBtn = document.getElementById('mobile-search-btn');
    const searchModal = document.getElementById('search-modal');
    const closeModal = document.getElementById('close-search-modal');
    
    if (searchBtn && searchModal && closeModal) {
        searchBtn.addEventListener('click', () => {
            searchModal.classList.remove('hidden');
            searchModal.classList.add('flex');
        });
        
        closeModal.addEventListener('click', () => {
            searchModal.classList.add('hidden');
            searchModal.classList.remove('flex');
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && searchModal.classList.contains('flex')) {
                searchModal.classList.add('hidden');
                searchModal.classList.remove('flex');
            }
        });
    }
});