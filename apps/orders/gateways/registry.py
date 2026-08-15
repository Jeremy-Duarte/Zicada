from typing import Dict, Type

from apps.orders.gateways.base import PaymentGateway

_GATEWAYS: Dict[str, Type[PaymentGateway]] = {}


def register_gateway(gateway_class: Type[PaymentGateway]) -> Type[PaymentGateway]:
    _GATEWAYS[gateway_class.name] = gateway_class
    return gateway_class


def get_gateway(name: str) -> PaymentGateway:
    gateway_class = _GATEWAYS.get(name)
    if not gateway_class:
        raise ValueError(f'Gateway desconocido: {name}')
    return gateway_class()


def list_gateways() -> Dict[str, Type[PaymentGateway]]:
    return _GATEWAYS.copy()
