/**
 * DeliveryComponents - Genera HTML consistente con los templates Django
 * Debe mantenerse sincronizado con delivery/components/atoms/*
 */
const DeliveryComponents = {
  orderCard(order) {
    const statusColors = this._statusColors(order.status);
    const paymentLabel = order.payment_status === 'pending' ? 'Pago pendiente'
      : order.payment_status === 'paid' ? 'Pagado'
      : 'Pago en linea';
    const paymentColors = this._paymentColors(order.payment_status);

    return `
      <a href="/delivery/orders/${order.id}/"
         class="block bg-white rounded-xl shadow-sm hover:shadow-md active:scale-[0.98] transition-all overflow-hidden mb-3">
        <div class="p-4">
          <div class="flex items-start justify-between mb-2">
            <div class="min-w-0 flex-1 mr-2">
              <h3 class="font-semibold text-gray-900 truncate">Pedido #${order.id}</h3>
              <p class="text-xs text-gray-500 truncate mt-0.5">${this._escapeHtml(order.address || '')}</p>
            </div>
            <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${statusColors.bg} ${statusColors.text}">
              <i class="fas fa-circle text-[0.5rem] mr-1.5 ${statusColors.dot}"></i>
              ${this._escapeHtml(order.status_label || order.status)}
            </span>
          </div>
          <div class="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-500">${order.items_count || 0} productos</span>
              <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${paymentColors.bg} ${paymentColors.text}">
                ${paymentLabel}
              </span>
            </div>
            <span class="text-lg font-bold text-gray-900">$${order.total || 0}</span>
          </div>
        </div>
      </a>
    `;
  },

  statusBadge(status, label) {
    const c = this._statusColors(status);
    return `<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}">
      <i class="fas fa-circle text-[0.5rem] mr-1.5 ${c.dot}"></i>${this._escapeHtml(label || status)}</span>`;
  },

  paymentBadge(paymentStatus) {
    const c = this._paymentColors(paymentStatus);
    const label = paymentStatus === 'pending' ? 'Pago pendiente'
      : paymentStatus === 'paid' ? 'Pagado'
      : 'Pago en linea';
    return `<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}">${label}</span>`;
  },

  emptyState({ icon = 'fas fa-box-open', title, description, actionUrl, actionText }) {
    let html = `<div class="text-center py-16 px-4">
      <div class="w-24 h-24 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
        <i class="${icon} text-gray-400 text-3xl"></i>
      </div>
      <h3 class="text-lg font-semibold text-gray-900 mb-1">${this._escapeHtml(title)}</h3>`;
    if (description) {
      html += `<p class="text-sm text-gray-500 mb-6">${this._escapeHtml(description)}</p>`;
    }
    if (actionUrl) {
      html += `<a href="${actionUrl}" class="inline-block bg-black text-white px-6 py-3 rounded-xl font-semibold hover:bg-gray-900 transition">${this._escapeHtml(actionText)}</a>`;
    }
    html += `</div>`;
    return html;
  },

  _statusColors(status) {
    const colors = {
      listo: { bg: 'bg-yellow-100', text: 'text-yellow-800', dot: 'text-yellow-500' },
      en_camino: { bg: 'bg-blue-100', text: 'text-blue-800', dot: 'text-blue-500' },
      entregado: { bg: 'bg-green-100', text: 'text-green-800', dot: 'text-green-500' },
      cancelado: { bg: 'bg-red-100', text: 'text-red-800', dot: 'text-red-500' },
    };
    return colors[status] || { bg: 'bg-gray-100', text: 'text-gray-800', dot: 'text-gray-500' };
  },

  _paymentColors(status) {
    const colors = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
      paid: { bg: 'bg-green-100', text: 'text-green-800' },
      online: { bg: 'bg-blue-100', text: 'text-blue-800' },
    };
    return colors[status] || { bg: 'bg-gray-100', text: 'text-gray-800' };
  },

  _escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
};
