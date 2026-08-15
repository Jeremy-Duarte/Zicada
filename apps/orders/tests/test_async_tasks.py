import time
from unittest import mock

import pytest

from apps.orders.async_tasks import get_async_backend, run_async


@pytest.mark.django_db
class TestAsyncBackend:
    def test_default_backend_is_sync(self):
        assert get_async_backend() == 'sync'

    def test_sync_backend_runs_inline(self):
        calls = []

        def fake(*args, **kwargs):
            calls.append(args)

        run_async(fake, 1, 2)
        assert calls == [(1, 2)]

    def test_threading_backend_runs_in_background(self):
        done = []

        def slow(*args, **kwargs):
            time.sleep(0.2)
            done.append(args)

        with mock.patch('apps.orders.async_tasks.get_async_backend', return_value='threading'):
            run_async(slow, 'x')

        assert done == []
        time.sleep(0.4)
        assert done == [('x',)]

    def test_celery_backend_uses_delay(self):
        def fake(*args, **kwargs):
            pass

        fake.delay = mock.MagicMock()
        with mock.patch('apps.orders.async_tasks.get_async_backend', return_value='celery'):
            run_async(fake, 'a', 'b')

        fake.delay.assert_called_once_with('a', 'b')
