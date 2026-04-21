from .models import Order

def generate_order_number():
    # Genera número de pedido en formato ZCD-0001, ZCD-0002... ZCE-0001...
    last_order = Order.objects.order_by('-id').first()
    
    if not last_order:
        return "ZCD-0001"
    
    last_number = last_order.order_number
    prefix = last_number[:3]
    num = int(last_number[4:])
    
    if num >= 9999:
        # Incrementar prefijo: ZCD -> ZCE -> ZCF
        new_prefix = f"ZC{chr(ord(prefix[2]) + 1)}"
        return f"{new_prefix}-0001"
    
    return f"{prefix}-{str(num + 1).zfill(4)}"