import logging
from decimal import Decimal
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from apps.products.models import ProductVariant
from apps.orders.constants import FREE_SHIPPING_THRESHOLD, DEFAULT_SHIPPING_COST, CART_EXPIRATION_DAYS, MAX_QUANTITY_PER_ITEM

logger = logging.getLogger(__name__)


class Cart:
    """
    Gestor del carrito de compras usando almacenamiento en sesión de Django.
    Maneja selección de productos, control de cantidades, precios, envío,
    validación de inventario y creación de pedidos con seguridad de concurrencia.
    """

    # Constantes configurables (reemplazables desde settings)

    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = {'items': {}, 'updated_at': None}
        self.cart = cart
        self.FREE_SHIPPING_THRESHOLD = FREE_SHIPPING_THRESHOLD
        self.DEFAULT_SHIPPING_COST = DEFAULT_SHIPPING_COST
        self.CART_EXPIRATION_DAYS = CART_EXPIRATION_DAYS
        self.MAX_QUANTITY_PER_ITEM = MAX_QUANTITY_PER_ITEM
        # Limpia carritos expirados en memoria sin forzar una escritura en la sesión
        self._clean_if_expired()

    def save(self):
        """Persiste el estado del carrito en la sesión con una marca de tiempo actual."""
        self.cart['updated_at'] = timezone.now().isoformat()
        self.session['cart'] = self.cart
        self.session.modified = True

    def _clean_if_expired(self):
        """
        Limpia el contenido del carrito si supera CART_EXPIRATION_DAYS.
        Los cambios se aplican solo en memoria; el siguiente save() persistirá el carrito vacío.
        """
        updated_at = self.cart.get('updated_at')
        if not updated_at:
            return
        try:
            last_updated = timezone.datetime.fromisoformat(updated_at)
            if timezone.now() - last_updated > timedelta(days=self.CART_EXPIRATION_DAYS):
                self.cart['items'] = {}
                self.cart['updated_at'] = None
                logger.info("Cart expired and cleared in memory (last update: %s).", last_updated)
        except (ValueError, TypeError):
            self.cart['items'] = {}
            self.cart['updated_at'] = None
            logger.warning("Cart with invalid timestamp cleared in memory.")

    def _get_variant_or_error(self, variant_id):
        """
        Obtiene un ProductVariant activo con su producto, talla y color relacionados.
        Lanza ValidationError si la variante no se encuentra.
        """
        try:
            return ProductVariant.objects.select_related(
                'product', 
                'size', 
                'product_color',
                'product_color__color'
            ).get(id=variant_id, is_active=True)
        except ProductVariant.DoesNotExist:
            logger.warning("Attempt to access unavailable variant (id=%s).", variant_id)
            raise ValidationError(
                'El producto que intentas agregar ya no está disponible. '
                'Por favor, verifica la lista de productos.'
            )

    def _normalize_variant_id(self, variant_id):
        """Garantiza que el ID de la variante sea un entero válido; lanza excepción en caso contrario."""
        try:
            return int(variant_id)
        except (TypeError, ValueError):
            raise ValidationError('El identificador del producto no es válido.')

    def add(self, variant_id, quantity=1):
        """
        Agrega una variante de producto al carrito.
        Valida disponibilidad de inventario, aplica límites de cantidad por artículo,
        y almacena el precio como cadena para evitar pérdida de precisión decimal.
        """
        variant_id = self._normalize_variant_id(variant_id)

        if not isinstance(quantity, int) or quantity < 1:
            raise ValidationError('La cantidad debe ser un número entero positivo.')

        if quantity > MAX_QUANTITY_PER_ITEM:
            raise ValidationError(
                f'No puedes agregar más de {MAX_QUANTITY_PER_ITEM} '
                f'unidades del mismo producto.'
            )

        variant = self._get_variant_or_error(variant_id)
        items = self.cart['items']
        item_key = str(variant_id)
        current_qty = items[item_key]['quantity'] if item_key in items else 0
        new_qty = current_qty + quantity

        if variant.stock == 0:
            logger.warning("Out of stock (id=%s, name=%s).", variant_id, variant.product.name)
            raise ValidationError(
                f'Lo sentimos, "{variant.product.name}" ({variant.size.name}, '
                f'{variant.product_color.color.name}) está agotado.'
            )

        if variant.stock < new_qty:
            max_extra = variant.stock - current_qty
            raise ValidationError(
                f'No tenemos suficiente stock de "{variant.product.name}" '
                f'({variant.size.name}, {variant.product_color.color.name}). '
                f'Disponible: {variant.stock}. '
                f'Ya tienes {current_qty} en el carrito. '
                f'Puedes agregar hasta {max_extra} más.'
            )

        featured_image = ''
        if variant.product_color.featured_image:
            featured_image = variant.product_color.featured_image.image.url
        elif variant.product_color.images.exists():
            featured_image = variant.product_color.images.first().image.url

        if item_key in items:
            items[item_key]['quantity'] = new_qty
        else:
            items[item_key] = {
                'variant_id': variant.id,
                'product_name': variant.product.name,
                'size_name': variant.size.name,
                'color_name': variant.product_color.color.name,
                'color_code': variant.product_color.color.code or '#cccccc',
                'price': str(variant.product.price),
                'quantity': quantity,
                'image': featured_image,
                'stock': variant.stock,
            }

        self.save()
        return self.get_item(item_key)

    def remove(self, variant_id):
        """Elimina una variante del carrito. Retorna True si el artículo existía."""
        variant_id = self._normalize_variant_id(variant_id)
        item_key = str(variant_id)
        if item_key in self.cart['items']:
            del self.cart['items'][item_key]
            self.save()
            logger.info("Variant %s removed from cart.", variant_id)
            return True
        logger.warning("Attempt to remove non‑existent variant %s.", variant_id)
        return False

    def update_quantity(self, variant_id, quantity):
        """
        Actualiza la cantidad de un producto que ya está en el carrito.
        Bloquea la fila de la variante (select_for_update) para evitar condiciones de carrera
        al verificar la disponibilidad de inventario.
        """
        variant_id = self._normalize_variant_id(variant_id)

        if not isinstance(quantity, int) or quantity < 1:
            if quantity < 1:
                return self.remove(variant_id)
            raise ValidationError('La cantidad debe ser un número entero positivo.')

        if quantity > self.MAX_QUANTITY_PER_ITEM:
            raise ValidationError(
                f'La cantidad no puede superar {self.MAX_QUANTITY_PER_ITEM} unidades.'
            )

        item_key = str(variant_id)
        if item_key not in self.cart['items']:
            raise ValidationError('El producto no está en tu carrito.')

        with transaction.atomic():
            variant = ProductVariant.objects.select_for_update().select_related(
                'product', 'size', 'product_color', 'product_color__color'
            ).get(id=variant_id, is_active=True)
            
            if variant.stock < quantity:
                raise ValidationError(
                    f'Stock insuficiente para "{variant.product.name}" '
                    f'({variant.size.name}, {variant.product_color.color.name}). '
                    f'Disponible: {variant.stock}.'
                )
            self.cart['items'][item_key]['quantity'] = quantity
            self.save()
            return self.get_item(item_key)

    def get_item(self, variant_id):
        """Retorna el diccionario del artículo del carrito para una variante, o None."""
        variant_id = self._normalize_variant_id(variant_id)
        item_key = str(variant_id)
        return self.cart['items'].get(item_key)

    def get_items(self):
        """Retorna todos los artículos del carrito como una lista de diccionarios."""
        return list(self.cart['items'].values())

    def get_total_items(self):
        """Número total de unidades (suma de todas las cantidades)."""
        return sum(item['quantity'] for item in self.cart['items'].values())

    def get_subtotal(self):
        """
        Subtotal del carrito (sin envío).
        Los precios se convierten de cadena a Decimal para evitar errores de coma flotante.
        """
        return Decimal(sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart['items'].values()
        ))

    def get_shipping_cost(self):
        """
        Retorna el costo de envío.
        Se aplica envío gratis cuando el subtotal alcanza o supera FREE_SHIPPING_THRESHOLD.
        """
        if self.get_subtotal() >= self.FREE_SHIPPING_THRESHOLD:
            return Decimal(0)
        return Decimal(DEFAULT_SHIPPING_COST)

    def get_total(self):
        """Monto total del carrito (subtotal + envío)."""
        return self.get_subtotal() + self.get_shipping_cost()

    def get_summary(self):
        """Retorna un diccionario con toda la información del carrito para las plantillas."""
        return {
            'items': self.get_items(),
            'subtotal': self.get_subtotal(),
            'shipping_cost': self.get_shipping_cost(),
            'total': self.get_total(),
            'total_items': self.get_total_items(),
            'is_empty': self.is_empty(),
        }

    def clear(self):
        """Vacía el carrito y registra la acción."""
        self.cart['items'] = {}
        self.save()
        logger.info("Cart emptied (session_key: %s).", self.session.session_key)

    def is_empty(self):
        """Verifica si el carrito no contiene artículos."""
        return len(self.cart['items']) == 0

    def validate_stock(self):
        """
        Verifica todos los artículos del carrito contra la base de datos actual para inventario y existencia.
        Retorna una lista de diccionarios de error para cualquier inconsistencia.
        """
        errors = []
        for item in self.get_items():
            try:
                variant = ProductVariant.objects.select_related(
                    'product', 'size', 'product_color', 'product_color__color'
                ).get(id=item['variant_id'], is_active=True)
                if variant.stock < item['quantity']:
                    errors.append({
                        'name': item['product_name'],
                        'size': item['size_name'],
                        'color': item['color_name'],
                        'available': variant.stock,
                        'requested': item['quantity']
                    })
                    logger.warning(
                        "Insufficient stock for %s (%s, %s): requested %d, available %d.",
                        item['product_name'], item['size_name'], item['color_name'],
                        item['quantity'], variant.stock
                    )
            except ProductVariant.DoesNotExist:
                errors.append({
                    'name': item['product_name'],
                    'size': item['size_name'],
                    'color': item['color_name'],
                    'available': 0,
                    'requested': item['quantity']
                })
                logger.error("Variant %d not found for product '%s'.", item['variant_id'], item['product_name'])
        return errors

    def to_order_items(self, order):
        """
        Convierte los artículos del carrito en objetos OrderItem, reduce el inventario atómicamente
        y luego vacía el carrito.
        Realiza una verificación final de inventario bajo una transacción de base de datos con bloqueos
        pesimistas de fila (select_for_update) para garantizar consistencia.
        """
        from .models import OrderItem

        stock_errors = self.validate_stock()
        if stock_errors:
            error_messages = [
                f'"{err["name"]}" ({err["size"]}, {err["color"]}): '
                f'disponible {err["available"]}, solicitado {err["requested"]}'
                for err in stock_errors
            ]
            raise ValidationError(
                'No se pudo procesar el pedido porque algunos productos '
                'no tienen suficiente stock:\n' + '\n'.join(error_messages)
            )

        with transaction.atomic():
            order_items = []
            for item in self.get_items():
                try:
                    # Bloquea y carga la variante, asegurando que siga activa
                    variant = ProductVariant.objects.select_related(
                        'product', 'size', 'product_color', 'product_color__color'
                    ).get(id=item['variant_id'], is_active=True)
                except ProductVariant.DoesNotExist:
                    logger.error("Variant %d vanished during order creation.", item['variant_id'])
                    raise ValidationError(
                        f'El producto "{item["product_name"]}" ya no está disponible. '
                        'Actualiza tu carrito.'
                    )

                if variant.stock < item['quantity']:
                    logger.warning(
                        "Stock conflict at order time for %s: need %d, have %d.",
                        item['product_name'], item['quantity'], variant.stock
                    )
                    raise ValidationError(
                        f'Error de inventario para "{variant.product.name}". '
                        'Intenta de nuevo.'
                    )

                variant.stock -= item['quantity']
                variant.save(update_fields=['stock'])

                order_item = OrderItem(
                    order=order,
                    variant=variant,
                    product_name_snapshot=item['product_name'],
                    size_snapshot=item['size_name'],
                    quantity=item['quantity'],
                    unit_price=Decimal(item['price']),
                    stock_snapshot=variant.stock,
                    subtotal=Decimal(item['price']) * item['quantity']
                )
                order_items.append(order_item)

            OrderItem.objects.bulk_create(order_items)
            self.clear()

        return order_items