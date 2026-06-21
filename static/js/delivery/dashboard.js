// Dashboard.js
(function() {
    'use strict';
    console.log('Dashboard loaded');

    // Comprobar si la app ya está instalada o ejecutándose en modo autónomo (standalone)
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
    
    if (isStandalone) {
        console.log('Zicada Delivery ejecutándose en modo PWA instalado.');
        return;
    }

    // --- INSTALACIÓN PARA ANDROID / CHROME / EDGE ---
    let deferredPrompt = null;
    const installBanner = document.getElementById('pwa-install-banner');
    const installBtn = document.getElementById('pwa-install-btn');

    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevenir el prompt automático de instalación
        e.preventDefault();
        // Guardar el evento para poder dispararlo luego
        deferredPrompt = e;
        // Mostrar el banner de instalación en la UI
        if (installBanner) {
            installBanner.classList.remove('hidden');
        }
    });

    if (installBtn) {
        installBtn.addEventListener('click', async () => {
            if (!deferredPrompt) return;
            
            // Mostrar la ventana nativa de instalación
            deferredPrompt.prompt();
            
            // Esperar la respuesta del usuario
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`Respuesta del usuario al prompt de instalación: ${outcome}`);
            
            // Descartar el prompt para que no pueda usarse de nuevo
            deferredPrompt = null;
            
            // Ocultar el banner
            if (installBanner) {
                installBanner.classList.add('hidden');
            }
        });
    }

    // --- INSTALACIÓN PARA IOS (IPHONE / IPAD - SAFARI) ---
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    // Comprobar si es Safari en iOS
    const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
    const iosInstallBanner = document.getElementById('pwa-ios-install-banner');

    if (isIOS && isSafari && iosInstallBanner) {
        // Mostrar instrucciones personalizadas para iOS
        iosInstallBanner.classList.remove('hidden');
    }
})();
