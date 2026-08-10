import pytest
import tempfile
from PIL import Image as PILImage
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from io import BytesIO

from apps.core.models import GalleryLayout, GalleryPhoto


@pytest.fixture
def local_storage(settings):
    """Usa almacenamiento local de archivos para evitar llamadas a Cloudinary."""
    tmpdir = tempfile.mkdtemp()
    storage = FileSystemStorage(location=tmpdir)
    image_field = GalleryPhoto._meta.get_field('image')
    original_storage = image_field.storage
    image_field.storage = storage
    original_storages = settings.STORAGES.copy()
    settings.STORAGES['default'] = {'BACKEND': 'django.core.files.storage.FileSystemStorage', 'OPTIONS': {'location': tmpdir}}
    yield storage
    image_field.storage = original_storage
    settings.STORAGES = original_storages


def _create_image(width: int = 600, height: int = 400, color: tuple = (255, 0, 0)):
    """Crea una imagen en memoria para usar en tests."""
    image = PILImage.new('RGB', (width, height), color)
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f'test_{width}x{height}.jpg')


@pytest.mark.django_db
class TestGalleryLayoutModel:
    def test_create_layout(self):
        layout = GalleryLayout.objects.create(
            name='Grid 2x2',
            columns=2,
            rows=2,
            css_class='grid-cols-2',
            max_photos=4,
        )
        assert layout.capacity() == 4
        assert str(layout) == 'Grid 2x2'

    def test_clean_validates_capacity(self):
        layout = GalleryLayout(
            name='Grid 2x2',
            columns=2,
            rows=2,
            max_photos=9,
        )
        with pytest.raises(Exception):
            layout.full_clean()


@pytest.mark.django_db
class TestGalleryPhotoModel:
    def test_create_photo_computes_aspect_ratio(self, local_storage):
        layout = GalleryLayout.objects.create(
            name='Grid 3x3',
            columns=3,
            rows=3,
            css_class='grid-cols-3',
            max_photos=9,
        )
        photo = GalleryPhoto.objects.create(
            image=_create_image(600, 400),
            alt_text='Foto horizontal',
            layout=layout,
        )
        assert photo.aspect_ratio == pytest.approx(1.5, 0.1)
        assert photo.aspect_category == GalleryPhoto.ASPECT_LANDSCAPE
        assert 'col-span-2' in photo.display_zone

    def test_portrait_aspect_category(self, local_storage):
        photo = GalleryPhoto.objects.create(
            image=_create_image(400, 800),
            alt_text='Foto vertical',
        )
        assert photo.aspect_category == GalleryPhoto.ASPECT_PORTRAIT
        assert photo.display_zone == 'col-span-1'

    def test_wide_aspect_category(self, local_storage):
        photo = GalleryPhoto.objects.create(
            image=_create_image(1200, 400),
            alt_text='Foto panoramica',
        )
        assert photo.aspect_category == GalleryPhoto.ASPECT_WIDE
        assert photo.display_zone == 'col-span-2'

    def test_square_aspect_category(self, local_storage):
        photo = GalleryPhoto.objects.create(
            image=_create_image(500, 500),
            alt_text='Foto cuadrada',
        )
        assert photo.aspect_category == GalleryPhoto.ASPECT_SQUARE
        assert photo.display_zone == 'col-span-1'

    def test_native_aspect_ratio_css(self, local_storage):
        photo = GalleryPhoto.objects.create(
            image=_create_image(600, 400),
            alt_text='Foto horizontal',
        )
        assert photo.native_aspect_ratio_css == '1.5'

    def test_native_aspect_ratio_css_defaults_to_square(self):
        photo = GalleryPhoto(alt_text='Foto sin imagen')
        assert photo.native_aspect_ratio_css == '1'

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
