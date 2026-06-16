// ==================== SERVICE WORKER - ZICADA DELIVERY (OPTIMIZADO) ====================

// Usar globalThis en lugar de self (mejor compatibilidad)
// S2737: Usar Set para búsquedas de existencia
const ALLOWED_ORIGINS = new Set([
    globalThis.location?.origin || 'http://localhost:8000',
    'https://zicada-delivery.onrender.com',
    'https://zicada-delivery.railway.app'
]);

// Variables que serán reemplazadas en tiempo de registro
let CACHE_NAME = 'zicada-delivery-default';
let OFFLINE_URL = '/delivery/offline/';
let PRECACHE_URLS = [];
let SW_VERSION = '1.0.0';

/**
 * Verifica si un origen está permitido
 * Set.has() es O(1) vs Array.includes() que es O(n)
 * @param {string} origin - Origen a verificar
 * @returns {boolean} True si está permitido
 */
function isOriginAllowed(origin) {
    return ALLOWED_ORIGINS.has(origin);
}

// Escuchar mensaje con la configuración del cliente (con verificación de origen)
globalThis.addEventListener('message', function(event) {
    // S2819: Verificar origen del mensaje
    if (!isOriginAllowed(event.origin)) {
        console.warn('[SW] Mensaje rechazado desde origen no autorizado:', event.origin);
        return;
    }
    
    // S6582: Usar optional chaining
    const configType = event.data?.type;
    
    if (configType === 'CONFIG') {
        CACHE_NAME = event.data.cacheName || CACHE_NAME;
        OFFLINE_URL = event.data.offlineUrl || OFFLINE_URL;
        PRECACHE_URLS = event.data.precacheUrls || [];
        SW_VERSION = event.data.version || SW_VERSION;
        
        console.log('[SW] Configuración recibida:', CACHE_NAME, 'v' + SW_VERSION);
        
        // Iniciar cacheo después de recibir configuración
        initializeCache();
    }
});

/**
 * Inicializa el cacheo de recursos
 */
async function initializeCache() {
    if (PRECACHE_URLS.length === 0) {
        console.warn('[SW] No hay URLs para precachear');
        return;
    }
    
    try {
        const cache = await caches.open(CACHE_NAME);
        console.log('[SW] Cacheando recursos:', PRECACHE_URLS);
        await cache.addAll(PRECACHE_URLS);
        console.log('[SW] Cache completado');
        await globalThis.skipWaiting();
    } catch (error) {
        console.error('[SW] Error en cache:', error);
    }
}

// Evento de instalación
globalThis.addEventListener('install', function(event) {
    console.log('[SW] Instalando...');
    
    event.waitUntil(
        Promise.resolve().then(function() {
            console.log('[SW] Esperando configuración...');
        })
    );
});

// Evento de activación - limpiar caches viejas
globalThis.addEventListener('activate', function(event) {
    console.log('[SW] Activando...');
    
    event.waitUntil(
        caches.keys().then(async function(cacheNames) {
            const deletePromises = [];
            
            // S4138: Usar for...of
            for (const cacheName of cacheNames) {
                const isCurrentCache = cacheName === CACHE_NAME;
                const isOldZicadaCache = cacheName.startsWith('zicada-delivery-') && !isCurrentCache;
                
                if (isOldZicadaCache) {
                    console.log('[SW] Eliminando cache antigua:', cacheName);
                    deletePromises.push(caches.delete(cacheName));
                }
            }
            
            await Promise.all(deletePromises);
            console.log('[SW] Tomando control de los clientes');
            return globalThis.clients.claim();
        })
    );
});

/**
 * Estrategia: Network First con fallback a cache
 * @param {Request} request - La petición interceptada
 * @returns {Promise<Response>} La respuesta
 */
async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);
        
        // Cachear respuestas exitosas GET
        const isGetRequest = request.method === 'GET';
        const isSuccessfulResponse = networkResponse?.status === 200;
        
        if (isGetRequest && isSuccessfulResponse) {
            const cache = await caches.open(CACHE_NAME);
            // No esperar a que termine el cacheo para no bloquear la respuesta
            cache.put(request, networkResponse.clone()).catch(function(err) {
                console.warn('[SW] Error cacheando respuesta:', err);
            });
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network fallback a cache:', request.url);
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const isNavigation = request.mode === 'navigate';
        if (isNavigation) {
            const offlineResponse = await caches.match(OFFLINE_URL);
            if (offlineResponse) {
                return offlineResponse;
            }
        }
        
        return new Response('Offline - Recurso no disponible', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'text/plain'
            })
        });
    }
}

/**
 * Estrategia: Cache First con fallback a network
 * @param {Request} request - La petición interceptada
 * @returns {Promise<Response>} La respuesta
 */
async function cacheFirstStrategy(request) {
    try {
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        
        const isGetRequest = request.method === 'GET';
        const isSuccessfulResponse = networkResponse?.status === 200;
        
        if (isGetRequest && isSuccessfulResponse) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone()).catch(function(err) {
                console.warn('[SW] Error cacheando respuesta:', err);
            });
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[SW] Error en cache-first:', error);
        return new Response('Recurso no disponible', { status: 404 });
    }
}

/**
 * Determina la estrategia según el tipo de recurso
 * @param {Request} request - La petición
 * @returns {Promise<Response>} La respuesta
 */
function handleFetch(request) {
    const url = new URL(request.url);
    
    // Estrategia diferente para APIs
    const isApiRequest = url.pathname.startsWith('/delivery/api/');
    if (isApiRequest) {
        return networkFirstStrategy(request);
    }
    
    // Estrategia para archivos estáticos (CSS, JS, imágenes)
    const staticPattern = /\.(css|js|png|jpg|jpeg|svg|webp|woff2?|ttf|eot)$/i;
    const isStaticAsset = staticPattern.test(url.pathname);
    if (isStaticAsset) {
        return cacheFirstStrategy(request);
    }
    
    // Estrategia para navegación HTML
    const isNavigation = request.mode === 'navigate';
    if (isNavigation) {
        return networkFirstStrategy(request);
    }
    
    // Por defecto: Network First
    return networkFirstStrategy(request);
}

// Interceptar peticiones
globalThis.addEventListener('fetch', function(event) {
    event.respondWith(handleFetch(event.request));
});

// Sincronización en segundo plano (para reportar incidencias offline)
globalThis.addEventListener('sync', function(event) {
    if (event.tag === 'sync-incidences') {
        event.waitUntil(syncIncidences());
    }
});

/**
 * Sincroniza incidencias pendientes
 */
async function syncIncidences() {
    console.log('[SW] Sincronizando incidencias pendientes...');
    
    try {
        const cache = await caches.open('incidences-queue');
        const requests = await cache.keys();
        
        if (requests.length === 0) {
            console.log('[SW] No hay incidencias pendientes');
            return;
        }
        
        const syncPromises = [];
        
        for (const request of requests) {
            syncPromises.push(
                (async function() {
                    try {
                        const response = await fetch(request);
                        
                        if (response.ok) {
                            await cache.delete(request);
                            console.log('[SW] Incidencia sincronizada:', request.url);
                            return true;
                        }
                        return false;
                    } catch (error) {
                        console.error('[SW] Error sincronizando incidencia:', error);
                        return false;
                    }
                })()
            );
        }
        
        await Promise.all(syncPromises);
        
        // Notificar al cliente
        const clients = await globalThis.clients.matchAll();
        for (const client of clients) {
            client.postMessage({
                type: 'SYNC_COMPLETE',
                timestamp: Date.now(),
                origin: globalThis.location.origin
            });
        }
    } catch (error) {
        console.error('[SW] Error en syncIncidences:', error);
    }
}

// Notificaciones push
globalThis.addEventListener('push', function(event) {
    let data = {
        title: 'Zicada Delivery',
        body: 'Tienes nuevas actualizaciones en tu app de delivery',
        url: '/delivery/orders/'
    };
    
    if (event.data) {
        try {
            const parsedData = event.data.json();
            data = {
                title: parsedData.title || data.title,
                body: parsedData.body || data.body,
                url: parsedData.url || data.url,
                orderId: parsedData.orderId || null
            };
        } catch (error) {
            data.body = event.data.text() || data.body;
        }
    }
    
    const options = {
        body: data.body,
        icon: '/static/delivery/icons/icon-192x192.png',
        badge: '/static/delivery/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url,
            orderId: data.orderId || null
        },
        actions: [
            {
                action: 'view',
                title: 'Ver pedido'
            },
            {
                action: 'close',
                title: 'Cerrar'
            }
        ]
    };
    
    event.waitUntil(
        globalThis.registration.showNotification(data.title, options)
    );
});

// Manejador de clic en notificaciones
globalThis.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    if (event.action === 'view') {
        const urlToOpen = event.notification.data.url;
        
        event.waitUntil(
            globalThis.clients.matchAll({
                type: 'window',
                includeUncontrolled: true
            }).then(function(clientList) {
                for (const client of clientList) {
                    const isMatchingUrl = client.url === urlToOpen;
                    
                    if (isMatchingUrl && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                if (globalThis.clients.openWindow) {
                    return globalThis.clients.openWindow(urlToOpen);
                }
                
                console.warn('[SW] No se pudo abrir la ventana:', urlToOpen);
                return value;
            })
        );
    }
});

// Health check
globalThis.addEventListener('fetch', function(event) {
    const url = new URL(event.request.url);
    
    if (url.pathname === '/delivery/health/sw') {
        event.respondWith(
            new Response(JSON.stringify({
                status: 'ok',
                cacheName: CACHE_NAME,
                version: SW_VERSION,
                timestamp: Date.now()
            }), {
                headers: { 'Content-Type': 'application/json' }
            })
        );
    }
});