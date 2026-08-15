import logging
import threading
from typing import Any, Callable

from django.conf import settings
from django.db import close_old_connections

logger = logging.getLogger(__name__)

BACKEND_CELERY = 'celery'
BACKEND_THREADING = 'threading'
BACKEND_SYNC = 'sync'


def get_async_backend() -> str:
    """Retorna el backend de tareas asíncronas configurado."""
    return getattr(settings, 'ASYNC_BACKEND', BACKEND_SYNC)


def _run_in_thread(func: Callable, *args: Any, **kwargs: Any) -> None:
    """Ejecuta la función en un hilo daemon, cerrando conexiones DB al terminar."""

    def _target():
        close_old_connections()
        try:
            func(*args, **kwargs)
        except Exception:
            logger.exception('Error en tarea asíncrona (threading)')
        finally:
            close_old_connections()

    threading.Thread(target=_target, daemon=True).start()


def run_async(task: Callable, *args: Any, **kwargs: Any) -> None:
    """
    Despacha una tarea según el backend configurado (ASYNC_BACKEND).

    - celery: encola en el broker (requiere Redis + worker). La tarea debe
      tener el método .delay (tarea Celery registrada).
    - threading: ejecuta en un hilo en segundo plano (sin infraestructura).
    - sync: ejecuta en el mismo request (máxima economía, bloquea).

    `task` es invocable en cualquier modo; en modo celery además tiene .delay.
    """
    backend = get_async_backend()
    if backend == BACKEND_CELERY:
        task.delay(*args, **kwargs)
    elif backend == BACKEND_THREADING:
        _run_in_thread(task, *args, **kwargs)
    else:
        task(*args, **kwargs)
