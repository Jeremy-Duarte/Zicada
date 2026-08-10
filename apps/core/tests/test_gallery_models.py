import pytest
import tempfile
from PIL import Image as PILImage
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from io import BytesIO

from apps.core.models import GalleryPhoto


@pytest.fixture
def local_storage(settings):
    """Usa almacenamiento local de archivos para evitar llamadas a Cloudinary."""
    tmpdir = tempfile.mkdtemp()
    storage = FileSystemStorage(location=tmpdir)
    original_storages = settings.STORAGES.copy()
    settings.STORAGES['default'] = {'BACKEND': 'django.core.files.storage.FileSystemStorage', 'OPTIONS': {'location': tmpdir}}
    yield storage
    settings.STORAGES = original_storages


def _create_image(width: int = 600, height: int = 400, color: tuple = (255, 0, 0)):
    image = PILImage.new('RGB', (width, height), color)
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f'test_{width}x{height}.jpg')


@pytest.mark.django_db
class TestGalleryPhotoModel:
    def test_create_photo_defaults_to_1x1(self, local_storage):
        photo = GalleryPhoto.objects.create(
            image=_create_image(600, 400),
            alt_text='Foto horizontal',
        )
        assert photo.display_size == GalleryPhoto.DISPLAY_1X1
        assert 'col-span-2 row-span-1' in photo.display_classes()

    def test_set_2x2_display_size(self, local_storage):
        photo = GalleryPhoto.objects.create(
            image=_create_image(400, 800),
            alt_text='Foto vertical',
            display_size=GalleryPhoto.DISPLAY_2X2,
        )
        assert photo.display_size == GalleryPhoto.DISPLAY_2X2
        assert 'col-span-2 row-span-2' in photo.display_classes()

    def test_soft_delete_and_restore(self, local_storage):
        photo = GalleryPhoto.objects.create(
            image=_create_image(500, 500),
            alt_text='Foto',
        )
        photo.soft_delete()
        assert photo.is_active is False
        assert photo.deleted_at is not None

        photo.restore()
        assert photo.is_active is True
        assert photo.deleted_at is None
