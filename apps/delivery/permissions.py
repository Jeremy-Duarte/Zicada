from rest_framework.permissions import BasePermission


class IsDeliveryUser(BasePermission):
    """
    Permiso para verificar que el usuario es un entregador.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and getattr(request.user, 'is_delivery', False)