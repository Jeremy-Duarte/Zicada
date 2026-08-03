// ============================================
// COLLECTION ZONE EDITOR - JavaScript
// Canvas-based editor for clickable zones over images
// ============================================

(function () {
    'use strict';

    // ============================================
    // GLOBAL STATE
    // ============================================

    let ZoneEditorData;
    let zones = [];
    let uidCounter = 1;
    let selectedUid = null;
    let drawMode = false;
    let draw = null;
    let drag = null;
    let rafPending = false;
    let formTargetUid = null;
    let productTargetUid = null;

    // DOM elements, cached during init
    const el = {};

    const HANDLE_NAMES = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
    const MIN_SIZE = 1;

    const HANDLE_POSITIONS = {
        nw: { top: '-4px', left: '-4px', cursor: 'nwse-resize' },
        n: { top: '-4px', left: '50%', transform: 'translateX(-50%)', cursor: 'ns-resize' },
        ne: { top: '-4px', right: '-4px', cursor: 'nesw-resize' },
        e: { top: '50%', right: '-4px', transform: 'translateY(-50%)', cursor: 'ew-resize' },
        se: { bottom: '-4px', right: '-4px', cursor: 'nwse-resize' },
        s: { bottom: '-4px', left: '50%', transform: 'translateX(-50%)', cursor: 'ns-resize' },
        sw: { bottom: '-4px', left: '-4px', cursor: 'nesw-resize' },
        w: { top: '50%', left: '-4px', transform: 'translateY(-50%)', cursor: 'ew-resize' }
    };

    // ============================================
    // UTILITIES
    // ============================================

    function qs(selector) {
        return document.querySelector(selector);
    }

    function clampNum(value, min, max) {
        return Math.min(max, Math.max(min, value));
    }

    function round(value) {
        return Math.round(value * 100) / 100;
    }

    function findZoneByUid(uid) {
        return zones.find((zone) => zone.uid === uid) || null;
    }

    function findZoneByElement(target) {
        const uid = parseInt(target.closest('.zone-rect')?.dataset.uid, 10);
        return Number.isFinite(uid) ? findZoneByUid(uid) : null;
    }

    // ============================================
    // COORDINATE CONVERSION (px <-> %)
    // ============================================

    function imageRect() {
        return el.image.getBoundingClientRect();
    }

    function pxToPctX(px) {
        return (px / imageRect().width) * 100;
    }

    function pxToPctY(px) {
        return (px / imageRect().height) * 100;
    }

    // ============================================
    // ZONE GEOMETRY
    // ============================================

    function clampZone(zone) {
        zone.width = round(clampNum(zone.width, MIN_SIZE, 100));
        zone.height = round(clampNum(zone.height, MIN_SIZE, 100));
        zone.x = round(clampNum(zone.x, 0, 100 - zone.width));
        zone.y = round(clampNum(zone.y, 0, 100 - zone.height));
        return zone;
    }

    function markDirty(zone) {
        zone.dirty = true;
        updateSidebarItem(zone);
    }

    function zoneLabelText(zone) {
        if (zone.label) return zone.label;
        if (zone.product_name) return zone.product_name;
        return 'Zona ' + (zones.indexOf(zone) + 1);
    }

    // ============================================
    // ZONE ELEMENT RENDERING
    // ============================================

    function ensureZoneEl(zone) {
        if (!zone.el) {
            zone.el = createZoneEl(zone);
            el.canvas.appendChild(zone.el);
        }
        return zone.el;
    }

    function renderZones() {
        zones.forEach((zone) => {
            ensureZoneEl(zone);
            positionZoneEl(zone);
        });
    }

    function requestRender() {
        if (rafPending) return;
        rafPending = true;
        requestAnimationFrame(() => {
            rafPending = false;
            renderZones();
        });
    }

    function positionZoneEl(zone) {
        if (!zone.el) return;
        zone.el.style.left = zone.x + '%';
        zone.el.style.top = zone.y + '%';
        zone.el.style.width = zone.width + '%';
        zone.el.style.height = zone.height + '%';
        const label = zone.el.querySelector('.zone-label');
        if (label) label.textContent = zoneLabelText(zone);
    }

    function createZoneEl(zone) {
        const zoneEl = document.createElement('div');
        zoneEl.className = 'zone-rect';
        zoneEl.dataset.uid = zone.uid;
        Object.assign(zoneEl.style, {
            position: 'absolute',
            border: '2px solid rgba(255,255,255,0.9)',
            boxShadow: '0 0 0 1px rgba(0,0,0,0.4)',
            boxSizing: 'border-box',
            cursor: 'move'
        });

        const label = document.createElement('span');
        label.className = 'zone-label';
        Object.assign(label.style, {
            position: 'absolute',
            top: '-24px',
            left: '0',
            background: 'rgba(0,0,0,0.65)',
            color: '#fff',
            padding: '1px 6px',
            fontSize: '11px',
            borderRadius: '3px',
            whiteSpace: 'nowrap',
            pointerEvents: 'none'
        });
        zoneEl.appendChild(label);

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'zone-delete';
        deleteBtn.type = 'button';
        deleteBtn.innerHTML = '&times;';
        deleteBtn.title = 'Eliminar zona';
        Object.assign(deleteBtn.style, {
            position: 'absolute',
            top: '-11px',
            right: '-11px',
            width: '22px',
            height: '22px',
            lineHeight: '18px',
            background: '#ef4444',
            color: '#fff',
            border: '1px solid #fff',
            borderRadius: '50%',
            cursor: 'pointer',
            fontSize: '14px',
            zIndex: '11',
            opacity: '0'
        });
        zoneEl.appendChild(deleteBtn);

        HANDLE_NAMES.forEach((name) => zoneEl.appendChild(createHandle(name)));
        positionZoneEl(zone);
        return zoneEl;
    }

    function createHandle(name) {
        const handle = document.createElement('div');
        handle.className = 'zone-handle zone-handle-' + name;
        handle.dataset.handle = name;
        Object.assign(handle.style, {
            position: 'absolute',
            width: '8px',
            height: '8px',
            background: '#fff',
            border: '1px solid #c2a575',
            borderRadius: '2px',
            zIndex: '10',
            boxSizing: 'border-box'
        }, HANDLE_POSITIONS[name]);
        return handle;
    }

    function updateSelection() {
        zones.forEach((zone) => {
            const selected = zone.uid === selectedUid;
            zone.el?.classList.toggle('selected', selected);
            const del = zone.el?.querySelector('.zone-delete');
            if (del) del.style.opacity = selected ? '1' : '';
            if (zone.li) {
                zone.li.classList.toggle('selected', selected);
                zone.li.classList.toggle('border-zicada-accent', selected);
                zone.li.classList.toggle('bg-amber-50', selected);
            }
        });
    }

    function selectZone(uid) {
        selectedUid = uid;
        updateSelection();
    }

    function deselectZone() {
        selectedUid = null;
        updateSelection();
    }

    // ============================================
    // SIDEBAR RENDERING
    // ============================================

    function renderSidebar() {
        el.zoneList.innerHTML = '';
        if (!zones.length) {
            el.zoneList.innerHTML =
                '<li class="text-sm text-gray-400 text-center py-8">No hay zonas aún. Activa "Dibujar zona" para crear la primera.</li>';
            return;
        }
        zones.forEach((zone) => {
            const item = document.createElement('li');
            item.dataset.zoneId = zone.uid;
            item.className =
                'group flex items-start gap-3 px-3 py-2 rounded-lg border border-gray-200 bg-white hover:border-zicada-accent transition cursor-pointer';
            item.innerHTML = `
                <span class="mt-0.5 text-zicada-accent"><i class="fas fa-th-large"></i></span>
                <span class="flex-1 min-w-0">
                    <span class="zone-title block text-sm font-medium text-gray-700 truncate"></span>
                    <span class="zone-sub block text-xs text-gray-400 truncate"></span>
                </span>
                <span class="zone-badge text-[10px] font-semibold text-amber-600"></span>`;
            item.addEventListener('click', () => selectZone(zone.uid));
            zone.li = item;
            el.zoneList.appendChild(item);
            updateSidebarItem(zone);
        });
    }

    function updateSidebarItem(zone) {
        const item = zone.li;
        if (!item) return;
        item.querySelector('.zone-title').textContent = zoneLabelText(zone);
        item.querySelector('.zone-sub').textContent = zone.product_name
            ? zone.product_name + ' - ' + (zone.color_name || '')
            : 'Sin producto asignado';
        const badge = item.querySelector('.zone-badge');
        if (!zone.id) {
            badge.textContent = 'Nueva';
        } else if (zone.dirty) {
            badge.textContent = 'Sin guardar';
        } else {
            badge.textContent = '';
        }
    }

    // ============================================
    // PRODUCT PICKER
    // ============================================

    function collectProductOptions() {
        return Array.from(el.zoneProductSelect.options)
            .filter((opt) => opt.value)
            .map((opt) => ({ id: parseInt(opt.value, 10), name: opt.textContent.trim() }));
    }

    function renderProductResults(query) {
        const q = (query || '').trim().toLowerCase();
        const options = collectProductOptions().filter((opt) => !q || opt.name.toLowerCase().includes(q));
        el.productResults.innerHTML = '';
        if (!options.length) {
            el.productResults.innerHTML =
                '<p class="text-sm text-gray-400 text-center py-6">Sin resultados</p>';
            return;
        }
        options.forEach((opt) => {
            const row = document.createElement('button');
            row.type = 'button';
            row.className =
                'w-full text-left px-3 py-2 rounded-lg hover:bg-amber-50 border border-gray-200 hover:border-zicada-accent transition';
            row.dataset.productColorId = opt.id;
            row.textContent = opt.name;
            row.addEventListener('click', () => pickProduct(opt.id));
            el.productResults.appendChild(row);
        });
    }

    function pickProduct(id) {
        if (el.zoneProductSelect) el.zoneProductSelect.value = String(id);
        const zone = productTargetUid ? findZoneByUid(productTargetUid) : null;
        if (zone) {
            zone.product_color_id = id;
            const option = Array.from(el.zoneProductSelect.options)
                .find((opt) => opt.value === String(id));
            if (option) {
                const parts = option.textContent.split(' - ');
                zone.product_name = parts[0] || '';
                zone.color_name = parts.slice(1).join(' - ');
            }
            markDirty(zone);
            positionZoneEl(zone);
        }
        closeProductModal();
    }

    function openProductModal(uid) {
        productTargetUid = uid || null;
        el.productSearch.value = '';
        renderProductResults('');
        el.productModal.classList.remove('hidden');
        el.productSearch.focus();
    }

    function closeProductModal() {
        el.productModal.classList.add('hidden');
        productTargetUid = null;
    }

    // ============================================
    // ZONE FORM MODAL
    // ============================================

    function openZoneForm(uid) {
        formTargetUid = uid;
        const zone = findZoneByUid(uid);
        if (!zone) return;
        el.zoneLabelInput.value = zone.label || '';
        el.zoneProductSelect.value = zone.product_color_id ? String(zone.product_color_id) : '';
        el.zoneFormModal.classList.remove('hidden');
        el.zoneLabelInput.focus();
    }

    function closeZoneForm() {
        el.zoneFormModal.classList.add('hidden');
        formTargetUid = null;
    }

    function syncZoneProductName(zone) {
        const option = Array.from(el.zoneProductSelect.options)
            .find((opt) => opt.value === String(zone.product_color_id));
        if (option) {
            const parts = option.textContent.split(' - ');
            zone.product_name = parts[0] || '';
            zone.color_name = parts.slice(1).join(' - ');
        } else {
            zone.product_name = '';
            zone.color_name = '';
        }
    }

    function zonePayload(zone) {
        return {
            x: zone.x,
            y: zone.y,
            width: zone.width,
            height: zone.height,
            label: zone.label || '',
            product_color_id: zone.product_color_id
        };
    }

    function applySavedZone(zone, saved) {
        if (saved && typeof saved.x !== 'undefined') {
            zone.x = saved.x;
            zone.y = saved.y;
            zone.width = saved.width;
            zone.height = saved.height;
        }
        if (saved && saved.label !== undefined) zone.label = saved.label;
        if (saved && saved.product_color_id !== undefined) zone.product_color_id = saved.product_color_id;
        zone.dirty = false;
        positionZoneEl(zone);
        updateSidebarItem(zone);
    }

    async function saveZoneFromForm() {
        const zone = findZoneByUid(formTargetUid);
        if (!zone) {
            closeZoneForm();
            return;
        }
        zone.label = el.zoneLabelInput.value.trim();
        zone.product_color_id = el.zoneProductSelect.value
            ? parseInt(el.zoneProductSelect.value, 10)
            : null;
        syncZoneProductName(zone);
        closeZoneForm();

        if (!zone.id) {
            try {
                const data = await apiRequest('POST', ZoneEditorData.zonesUrl, zonePayload(zone));
                const saved = data.zone || data;
                if (saved && saved.id != null) zone.id = saved.id;
                applySavedZone(zone, saved);
                showStatus('Zona creada correctamente');
            } catch (err) {
                showStatus(err.message, true);
            }
        } else {
            markDirty(zone);
            showStatus('Cambios pendientes de guardar');
        }
    }

    function cancelZoneForm() {
        const zone = findZoneByUid(formTargetUid);
        if (zone && !zone.id) removeZone(zone);
        closeZoneForm();
        showStatus('Zona descartada');
    }

    // ============================================
    // DRAW MODE
    // ============================================

    function toggleDrawMode(force) {
        const next = typeof force === 'boolean' ? force : !drawMode;
        if (next === drawMode) return;
        drawMode = next;
        el.btnDraw.classList.toggle('active', drawMode);
        if (!drawMode) cancelDraw();
        deselectZone();
        if (drawMode) showStatus('Haz clic y arrastra sobre la imagen para dibujar una zona');
    }

    function cancelDraw() {
        if (draw) {
            draw.el.remove();
            draw = null;
        }
    }

    function startDraw(e) {
        const rect = imageRect();
        const startX = e.clientX - rect.left;
        const startY = e.clientY - rect.top;
        const temp = document.createElement('div');
        Object.assign(temp.style, {
            position: 'absolute',
            border: '2px dashed #c2a575',
            background: 'rgba(194,165,117,0.2)',
            pointerEvents: 'none'
        });
        el.canvas.appendChild(temp);
        draw = { startX, startY, currentX: startX, currentY: startY, el: temp };
        updateDrawRect();
    }

    function updateDrawRect() {
        Object.assign(draw.el.style, {
            left: Math.min(draw.startX, draw.currentX) + 'px',
            top: Math.min(draw.startY, draw.currentY) + 'px',
            width: Math.abs(draw.currentX - draw.startX) + 'px',
            height: Math.abs(draw.currentY - draw.startY) + 'px'
        });
    }

    function createDraftZone(leftPx, topPx, widthPx, heightPx) {
        const zone = {
            uid: uidCounter++,
            id: null,
            x: round(pxToPctX(leftPx)),
            y: round(pxToPctY(topPx)),
            width: round(pxToPctX(widthPx)),
            height: round(pxToPctY(heightPx)),
            label: '',
            product_color_id: null,
            product_name: '',
            color_name: '',
            dirty: true,
            el: null,
            li: null
        };
        clampZone(zone);
        zones.push(zone);
        renderZones();
        renderSidebar();
        updateSelection();
        return zone;
    }

    function endDraw(e) {
        if (!draw) return;
        const rect = imageRect();
        const endX = clampNum(e.clientX - rect.left, 0, rect.width);
        const endY = clampNum(e.clientY - rect.top, 0, rect.height);
        const x1 = clampNum(draw.startX, 0, rect.width);
        const y1 = clampNum(draw.startY, 0, rect.height);
        const leftPx = Math.min(x1, endX);
        const topPx = Math.min(y1, endY);
        const widthPx = Math.abs(endX - x1);
        const heightPx = Math.abs(endY - y1);

        draw.el.remove();
        draw = null;

        if (widthPx < 3 || heightPx < 3) return;

        const zone = createDraftZone(leftPx, topPx, widthPx, heightPx);
        openZoneForm(zone.uid);
    }

    // ============================================
    // MOVE / RESIZE
    // ============================================

    function startMove(e, zone) {
        drag = {
            type: 'move',
            zone,
            pointerX: e.clientX,
            pointerY: e.clientY,
            startX: zone.x,
            startY: zone.y
        };
    }

    function startResize(e, zone, handle) {
        drag = {
            type: 'resize',
            zone,
            handle,
            pointerX: e.clientX,
            pointerY: e.clientY,
            startX: zone.x,
            startY: zone.y,
            startWidth: zone.width,
            startHeight: zone.height
        };
    }

    function resizeZone(dragState, dxPx, dyPx) {
        const zone = dragState.zone;
        const handle = dragState.handle;
        const dx = pxToPctX(dxPx);
        const dy = pxToPctY(dyPx);
        const rightEdge = dragState.startX + dragState.startWidth;
        const bottomEdge = dragState.startY + dragState.startHeight;

        let x = dragState.startX;
        let y = dragState.startY;
        let width = dragState.startWidth;
        let height = dragState.startHeight;

        if (handle.includes('e')) width = dragState.startWidth + dx;
        if (handle.includes('s')) height = dragState.startHeight + dy;
        if (handle.includes('w')) {
            width = dragState.startWidth - dx;
            x = dragState.startX + dx;
            if (width < MIN_SIZE) {
                x = rightEdge - MIN_SIZE;
                width = MIN_SIZE;
            }
        }
        if (handle.includes('n')) {
            height = dragState.startHeight - dy;
            y = dragState.startY + dy;
            if (height < MIN_SIZE) {
                y = bottomEdge - MIN_SIZE;
                height = MIN_SIZE;
            }
        }

        zone.x = x;
        zone.y = y;
        zone.width = width;
        zone.height = height;
        clampZone(zone);
    }

    function onMouseMove(e) {
        if (draw) {
            draw.currentX = e.clientX;
            draw.currentY = e.clientY;
            updateDrawRect();
            return;
        }
        if (drag) {
            const dxPx = e.clientX - drag.pointerX;
            const dyPx = e.clientY - drag.pointerY;
            if (drag.type === 'move') {
                drag.zone.x = drag.startX + pxToPctX(dxPx);
                drag.zone.y = drag.startY + pxToPctY(dyPx);
                clampZone(drag.zone);
            } else {
                resizeZone(drag, dxPx, dyPx);
            }
            markDirty(drag.zone);
            requestRender();
        }
    }

    function onMouseUp(e) {
        if (draw) {
            endDraw(e);
            return;
        }
        if (drag) drag = null;
    }

    // ============================================
    // DELETE / SAVE / API
    // ============================================

    async function apiRequest(method, url, payload) {
        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': ZoneEditorData.csrftoken
            },
            body: payload ? JSON.stringify(payload) : null
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.detail || data.error || data.message || 'Error del servidor');
        }
        return data;
    }

    function removeZone(zone) {
        zones = zones.filter((z) => z.uid !== zone.uid);
        if (selectedUid === zone.uid) deselectZone();
        zone.el?.remove();
        zone.li?.remove();
        renderSidebar();
    }

    async function deleteZone(zone) {
        if (zone.id) {
            try {
                await apiRequest('DELETE', ZoneEditorData.zonesUrl + zone.id + '/', null);
            } catch (err) {
                showStatus(err.message, true);
                return;
            }
        }
        removeZone(zone);
        showStatus('Zona eliminada');
    }

    async function saveZone(zone) {
        const data = await apiRequest('PUT', ZoneEditorData.zonesUrl + zone.id + '/', zonePayload(zone));
        applySavedZone(zone, data.zone || data);
    }

    async function saveAll() {
        const unsaved = zones.filter((z) => !z.id);
        if (unsaved.length) {
            showStatus('Hay zonas sin guardar. Completa su configuración o elimínalas.', true);
            return;
        }
        const dirty = zones.filter((z) => z.dirty);
        if (!dirty.length) {
            showStatus('No hay cambios para guardar');
            return;
        }
        try {
            for (const zone of dirty) {
                await saveZone(zone);
            }
            showStatus('Se guardaron ' + dirty.length + ' zona(s) correctamente');
        } catch (err) {
            showStatus(err.message, true);
        }
    }

    function showStatus(message, isError) {
        if (!el.status) return;
        el.status.textContent = message;
        el.status.classList.toggle('text-red-600', !!isError);
        el.status.classList.toggle('text-green-600', !isError);
        window.clearTimeout(showStatus._timer);
        showStatus._timer = window.setTimeout(() => {
            el.status.textContent = '';
        }, 4000);
    }

    // ============================================
    // EVENTS
    // ============================================

    function onCanvasMouseDown(e) {
        const deleteBtn = e.target.closest('.zone-delete');
        if (deleteBtn) {
            e.preventDefault();
            const zone = findZoneByElement(deleteBtn);
            if (zone) deleteZone(zone);
            return;
        }
        if (drawMode) {
            e.preventDefault();
            startDraw(e);
            return;
        }
        const handle = e.target.closest('.zone-handle');
        const rectEl = e.target.closest('.zone-rect');
        if (handle) {
            e.preventDefault();
            const zone = findZoneByElement(handle);
            if (zone) {
                selectZone(zone.uid);
                startResize(e, zone, handle.dataset.handle);
            }
            return;
        }
        if (rectEl) {
            e.preventDefault();
            const zone = findZoneByElement(rectEl);
            if (zone) {
                selectZone(zone.uid);
                startMove(e, zone);
            }
            return;
        }
        deselectZone();
    }

    function onCanvasDoubleClick(e) {
        const rectEl = e.target.closest('.zone-rect');
        if (!rectEl) return;
        const zone = findZoneByElement(rectEl);
        if (zone) openProductModal(zone.uid);
    }

    function onKeyDown(e) {
        if (e.key === 'Escape') {
            if (!el.zoneFormModal.classList.contains('hidden')) {
                cancelZoneForm();
                return;
            }
            if (!el.productModal.classList.contains('hidden')) {
                closeProductModal();
                return;
            }
            toggleDrawMode(false);
            deselectZone();
            return;
        }
        if (e.key !== 'Delete') return;
        const tag = e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
        const zone = selectedUid ? findZoneByUid(selectedUid) : null;
        if (zone) deleteZone(zone);
    }

    function bindEvents() {
        el.btnDraw.addEventListener('click', () => toggleDrawMode());
        el.btnSave.addEventListener('click', saveAll);
        el.canvas.addEventListener('mousedown', onCanvasMouseDown);
        el.canvas.addEventListener('dblclick', onCanvasDoubleClick);
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
        document.addEventListener('keydown', onKeyDown);

        el.productSearch.addEventListener('input', (e) => renderProductResults(e.target.value));
        el.btnProductClose?.addEventListener('click', closeProductModal);
        el.productModal?.addEventListener('click', (e) => {
            if (e.target === el.productModal) closeProductModal();
        });

        el.btnZoneSave?.addEventListener('click', saveZoneFromForm);
        el.btnZoneCancel?.addEventListener('click', cancelZoneForm);
        el.btnZoneClose?.addEventListener('click', cancelZoneForm);
        el.zoneFormModal?.addEventListener('click', (e) => {
            if (e.target === el.zoneFormModal) cancelZoneForm();
        });
    }

    // ============================================
    // INITIALIZATION
    // ============================================

    function cacheElements() {
        el.image = document.getElementById('zone-image');
        el.canvas = document.getElementById('zone-canvas');
        el.zoneList = document.getElementById('zone-list');
        el.btnDraw = document.getElementById('btn-draw');
        el.btnSave = document.getElementById('btn-save');
        el.status = document.getElementById('zone-save-status');

        el.productModal = document.getElementById('product-modal');
        el.productSearch = document.getElementById('product-search');
        el.productResults = document.getElementById('product-results');
        el.btnProductClose = document.getElementById('btn-product-close');

        el.zoneFormModal = document.getElementById('zone-form-modal');
        el.zoneLabelInput = document.getElementById('zone-label-input');
        el.zoneProductSelect = document.getElementById('zone-product-select');
        el.btnZoneSave = document.getElementById('btn-zone-save');
        el.btnZoneCancel = document.getElementById('btn-zone-cancel');
        el.btnZoneClose = document.getElementById('btn-zone-close');
    }

    function hydrateZone(raw) {
        return clampZone({
            uid: uidCounter++,
            id: raw.id != null ? raw.id : null,
            x: raw.x,
            y: raw.y,
            width: raw.width,
            height: raw.height,
            label: raw.label || '',
            product_color_id: raw.product_color_id || null,
            product_name: raw.product_name || '',
            color_name: raw.color_name || '',
            dirty: false,
            el: null,
            li: null
        });
    }

    function init() {
        const dataEl = document.getElementById('zone-editor-data');
        if (!dataEl) return;
        try {
            ZoneEditorData = JSON.parse(dataEl.textContent);
        } catch (err) {
            return;
        }
        cacheElements();
        if (!el.image || !el.canvas) return;

        zones = (ZoneEditorData.zones || []).map(hydrateZone);
        renderZones();
        renderSidebar();
        updateSelection();
        renderProductResults('');
        bindEvents();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
