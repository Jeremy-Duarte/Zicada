import pytest
from django.urls import reverse
from django.test import Client

from apps.users.models import User


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username='admin_gallery',
        password='testpass123',
        email='admin_gallery@zicada.test',
        is_staff=True,
    )
    from django.contrib.auth.models import Group
    group, _ = Group.objects.get_or_create(name='Administrador')
    user.groups.add(group)
    return user


@pytest.mark.django_db
class TestGalleryPageView:
    def test_gallery_page_returns_200(self, client: Client):
        response = client.get(reverse('core:gallery'))
        assert response.status_code == 200

    def test_gallery_page_context(self, client: Client):
        response = client.get(reverse('core:gallery'))
        assert 'gallery_photos' in response.context


@pytest.mark.django_db
class TestGalleryPhotoCRUD:
    def test_photo_list_requires_login(self, client: Client):
        response = client.get(reverse('core:gallery_photo_list'))
        assert response.status_code == 302

    def test_photo_list_accessible_by_admin(self, client: Client, admin_user):
        client.force_login(admin_user)
        response = client.get(reverse('core:gallery_photo_list'))
        assert response.status_code == 200

    def test_photo_create_get(self, client: Client, admin_user):
        client.force_login(admin_user)
        response = client.get(reverse('core:gallery_photo_create'))
        assert response.status_code == 200
