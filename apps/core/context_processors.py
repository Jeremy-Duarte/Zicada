from apps.orders.cart import Cart

def cart_context(request):
    cart = Cart(request)
    return {
        'cart_total_items': cart.get_total_items(),
    }