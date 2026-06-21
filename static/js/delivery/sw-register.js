(function() {
    'use strict';
    
    /**
     * Obtiene la configuración del Service Worker desde el servidor
     * @returns {Promise<Object>} Configuración del SW
     */
    async function getServiceWorkerConfig() {
        try {
            const response = await fetch('/delivery/sw-config.json');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const config = await response.json();
            return config;
        } catch (error) {
            console.error('Error obteniendo configuración SW:', error);
            
            // Fallback con valores por defecto
            return {
                cacheName: 'zicada-delivery-v1',
                offlineUrl: '/delivery/offline/',
                precacheUrls: [
                    '/delivery/offline/',
                    '/delivery/login/',
                    '/delivery/dashboard/',
                    '/delivery/orders/',
                    '/delivery/summary/',
                    '/static/css/delivery/main.css'
                ]
            };
        }
    }
    
    /**
     * Registra el Service Worker
     */
    async function registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('Service Worker no soportado en este navegador');
            return;
        }
        
        try {
            // Obtener configuración
            const config = await getServiceWorkerConfig();
            
            // Registrar el SW
            const registration = await navigator.serviceWorker.register('/delivery/sw.js');
            
            console.log('Service Worker registrado con éxito:', registration.scope);
            
            // Esperar a que el SW esté activo
            if (registration.active) {
                sendConfigToSW(registration.active, config);
            } else if (registration.installing) {
                registration.installing.addEventListener('statechange', function(event) {
                    const sw = event.target;
                    if (sw.state === 'activated') {
                        sendConfigToSW(sw, config);
                    }
                });
            }
            
            // Configurar sincronización en segundo plano
            setupBackgroundSync(registration);
            
            // Configurar notificaciones push
            setupPushNotifications(registration);
            
            // Configurar actualizaciones periódicas
            setupPeriodicUpdates(registration);
            
        } catch (error) {
            console.error('Error registrando Service Worker:', error);
        }
    }
    
    /**
     * Envía la configuración al Service Worker
     * @param {ServiceWorker} sw - Service Worker instance
     * @param {Object} config - Configuración
     */
    function sendConfigToSW(sw, config) {
        sw.postMessage({
            type: 'CONFIG',
            cacheName: config.cacheName,
            offlineUrl: config.offlineUrl,
            precacheUrls: config.precacheUrls
        });
        
        console.log('Configuración enviada al SW');
    }
    
    /**
     * Configura sincronización en segundo plano
     * @param {ServiceWorkerRegistration} registration - SW registration
     */
    function setupBackgroundSync(registration) {
        if ('sync' in registration) {
            // Registrar sincronización de incidencias
            registration.sync.register('sync-incidences')
                .then(function() {
                    console.log('Background sync registrado para incidencias');
                })
                .catch(function(error) {
                    console.error('Error registrando background sync:', error);
                });
        }
    }
    
    /**
     * Configura notificaciones push
     * @param {ServiceWorkerRegistration} registration - SW registration
     */
    async function setupPushNotifications(registration) {
        if (!('pushManager' in registration)) {
            console.warn('Push notifications no soportadas');
            return;
        }
        
        try {
            // Verificar suscripción existente
            const subscription = await registration.pushManager.getSubscription();
            
            if (subscription) {
                console.log('Push subscription existente:', subscription.endpoint);
                return;
            }
            
            // Aquí se implementaría la suscripción a notificaciones
            // Por ahora, solo logueamos
            console.log('Notificaciones push disponibles');
            
        } catch (error) {
            console.error('Error configurando push notifications:', error);
        }
    }
    
    /**
     * Configura actualizaciones periódicas
     * @param {ServiceWorkerRegistration} registration - SW registration
     */
    function setupPeriodicUpdates(registration) {
        if ('periodicSync' in registration) {
            // Verificar permisos
            navigator.permissions.query({ name: 'periodic-background-sync' })
                .then(function(status) {
                    if (status.state === 'granted') {
                        registration.periodicSync.register('update-orders', {
                            minInterval: 60 * 60 * 1000 // Cada hora
                        });
                        console.log('Periodic sync registrado');
                    }
                })
                .catch(function(error) {
                    console.log('Periodic sync no disponible:', error);
                });
        }
    }
    
    // Registrar al cargar la página
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', registerServiceWorker);
    } else {
        registerServiceWorker();
    }
    
    // Detectar actualizaciones del SW
    let refreshing = false;
    
    navigator.serviceWorker.addEventListener('controllerchange', function() {
        if (refreshing) {
            return;
        }
        
        refreshing = true;
        console.log('Service Worker actualizado, recargando página...');
        globalThis.location.reload();
    });
    
    // Recibir mensajes del SW
    navigator.serviceWorker.addEventListener('message', function(event) {
        if (event.data && event.data.type === 'SYNC_COMPLETE') {
            console.log('Sincronización completada:', event.data.timestamp);
            
            // Mostrar notificación al usuario
            if (globalThis.showToast) {
                globalThis.showToast('Datos sincronizados con el servidor', 'success');
            }
        }
    });
    
})();