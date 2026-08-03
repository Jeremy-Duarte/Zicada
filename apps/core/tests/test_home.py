import pytest
from django.urls import reverse

from apps.core.models import Gallery, HomePromo


@pytest.mark.django_db
class TestHomeView:
    # UT - 005
    def test_home_returns_200(self, client):
        response = client.get(reverse('home'))
        assert response.status_code == 200

    # UT - 006
    def test_home_context_has_new_sections(self, client):
        response = client.get(reverse('home'))
        for key in ('hero_slides', 'featured_collections', 'promos', 'gallery_items'):
            assert key in response.context

    # UT - 007
    def test_home_context_no_longer_loads_products(self, client):
        response = client.get(reverse('home'))
        assert 'latest_products' not in response.context
        assert 'categories' not in response.context


@pytest.mark.django_db
class TestGalleryModel:
    # UT - 008
    def test_gallery_respects_active_manager(self):
        active = Gallery.objects.create(description='Foto activa', alt_text='alt')
        inactive = Gallery.objects.create(description='Foto inactiva', alt_text='alt', is_active=False)

        result = Gallery.objects.all()

        assert active in result
        assert inactive not in result

    # UT - 009
    def test_gallery_can_be_softdeleted(self):
        item = Gallery.objects.create(description='Foto', alt_text='alt')
        item.soft_delete()

        assert item.is_active is False
        assert item.deleted_at is not None


@pytest.mark.django_db
class TestHomePromoModel:
    # UT - 010
    def test_promo_respects_active_manager(self):
        active = HomePromo.objects.create(title='Promo activa')
        inactive = HomePromo.objects.create(title='Promo inactiva', is_active=False)

        result = HomePromo.objects.all()

        assert active in result
        assert inactive not in result

    # UT - 011
    def test_promo_str_fallback(self):
        promo = HomePromo.objects.create()
        assert str(promo) == f"Promo #{promo.pk}"
