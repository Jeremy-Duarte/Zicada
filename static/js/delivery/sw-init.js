// Configuracion global de la aplicacion
window.ZICADA = window.ZICADA || {};

window.ZICADA.URLS = {
    serviceWorker: window.ZICADA_URLS?.serviceWorker || '',
    manifest: window.ZICADA_URLS?.manifest || '',
    offline: window.ZICADA_URLS?.offline || '',
    apiBase: window.ZICADA_URLS?.apiBase || '',
    login: window.ZICADA_URLS?.login || '',
    dashboard: window.ZICADA_URLS?.dashboard || '',
    orders: window.ZICADA_URLS?.orders || '',
    summary: window.ZICADA_URLS?.summary || '',
    logout: window.ZICADA_URLS?.logout || '',
};

window.ZICADA.CONFIG = {
    userId: window.ZICADA_CONFIG?.userId || null,
    csrfEndpoint: window.ZICADA_CONFIG?.csrfEndpoint || '',
    isAuthenticated: window.ZICADA_CONFIG?.isAuthenticated || false,
    isDelivery: window.ZICADA_CONFIG?.isDelivery || false,
    userFullName: window.ZICADA_CONFIG?.userFullName || '',
    userName: window.ZICADA_CONFIG?.userName || '',
};

window.ZICADA.SETTINGS = {
    refreshInterval: 30000,
    version: "1.1.0",
    environment: window.ZICADA_SETTINGS?.environment || 'production',
};

// Registro del Service Worker
(function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
        console.warn('Service Worker no soportado en este navegador');
        return;
    }

    var swUrl = window.ZICADA?.URLS?.serviceWorker;

    if (!swUrl) {
        console.error('URL del Service Worker no configurada');
        return;
    }

    console.log('Registrando Service Worker en:', swUrl);

    navigator.serviceWorker.register(swUrl, { scope: '/delivery/' })
        .then(function(registration) {
            console.log('Service Worker registrado con exito:', registration.scope);

            fetch('/delivery/sw-config.json')
                .then(function(res) { return res.json(); })
                .then(function(config) {
                    config.type = 'CONFIG';
                    var sw = registration.active || registration.installing || registration.waiting;
                    if (sw) {
                        sw.postMessage(config);
                    }
                })
                .catch(function(err) { console.error('Error fetching SW config', err); });

            registration.update();

            registration.addEventListener('updatefound', function() {
                var newSW = registration.installing;
                console.log('Nuevo Service Worker encontrado');

                newSW.addEventListener('statechange', function() {
                    if (newSW.state === 'activated') {
                        console.log('Nuevo Service Worker activado');
                        if (window.showToast) {
                            window.showToast('Nueva version disponible. Recargando...', 'info');
                        }
                        setTimeout(function() {
                            window.location.reload();
                        }, 2000);
                    }
                });
            });
        })
        .catch(function(error) {
            console.error('Error al registrar Service Worker:', error);
        });

    navigator.serviceWorker.addEventListener('message', function(event) {
        var data = event.data;
        if (data && data.type === 'SYNC_COMPLETE') {
            console.log('Sincronizacion completada:', data.timestamp);
            if (window.showToast) {
                window.showToast('Datos sincronizados con el servidor', 'success');
            }
        }
    });

    var isRefreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', function() {
        if (isRefreshing) {
            return;
        }
        isRefreshing = true;
        console.log('Service Worker actualizado, recargando pagina...');
        window.location.reload();
    });

    setInterval(function() {
        if (navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({
                type: 'CHECK_UPDATE'
            });
        }
    }, 60 * 60 * 1000);
})();
