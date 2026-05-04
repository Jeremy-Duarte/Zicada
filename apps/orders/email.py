from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_order_confirmation_email(order):    
    subject = f"Zicada - Tu pedido {order.order_number} ha sido confirmado"
    
    context = {
        'order': order,
        'items': order.items.all(),
        'tracking_url': f"{settings.SITE_URL}/orders/tracking/{order.tracking_token}/",
    }
    
    text_message = render_to_string('orders/emails/order_confirmation.txt', context)
    html_message = render_to_string('orders/emails/order_confirmation.html', context)
    
    send_mail(
        subject=subject,
        message=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.customer_email],
        html_message=html_message,
        fail_silently=False,
    )