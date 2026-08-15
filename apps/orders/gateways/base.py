from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, Optional

from apps.orders.models import Order, Payment


class PaymentGateway(ABC):
    """Interfaz común para todas las pasarelas de pago."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identificador interno: 'stripe', 'wompi'."""
        raise NotImplementedError

    @abstractmethod
    def create_intent(
        self,
        order: Order,
        payment: Payment,
        success_url: str,
        cancel_url: str,
        request_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Crea la intención de pago en la pasarela.
        Retorna un dict con:
        - gateway_session_id: str
        - redirect_url: str
        - raw_response: dict
        """
        raise NotImplementedError

    @abstractmethod
    def verify_signature(self, request_body: bytes, signature: str, secret: str) -> bool:
        """Verifica la firma del webhook."""
        raise NotImplementedError

    @abstractmethod
    def parse_event(self, request_body: bytes, signature: str) -> Dict[str, Any]:
        """
        Parsea y normaliza el evento del webhook (firma ya verificada).
        Retorna un dict normalizado:
        - event_id: str
        - event_type: str
        - gateway_session_id: str
        - gateway_transaction_id: str
        - amount: int (unidad mínima de la pasarela)
        - currency: str
        - status: str ('approved' | 'rejected' | 'refunded' | 'pending')
        - metadata: dict
        - raw: dict
        """
        raise NotImplementedError

    @abstractmethod
    def get_event_id(self, event: Dict[str, Any]) -> str:
        """Retorna el identificador único del evento para idempotencia."""
        raise NotImplementedError

    @abstractmethod
    def refund(self, payment: Payment) -> Dict[str, Any]:
        """Ejecuta reembolso total."""
        raise NotImplementedError

    @abstractmethod
    def to_gateway_amount(self, amount: Decimal) -> int:
        """Convierte monto COP al formato requerido por la pasarela."""
        raise NotImplementedError

    @abstractmethod
    def from_gateway_amount(self, amount: int) -> Decimal:
        """Convierte monto de la pasarela a COP."""
        raise NotImplementedError
