import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.products.models import Collection, InteractiveZone, Product, ProductColor, Color


@pytest.fixture
def collection_with_interactive(db, ifactory):
    def _create(status='borrador'):
        collection = ifactory.create(
            Collection,
            name='Colección Test',
            is_active=True,
            status=status,
        )
        return collection
    return _create


@pytest.fixture
def product_color_with_collection(db, ifactory, collection_with_interactive):
    def _create(collection=None):
        collection = collection or collection_with_interactive(status='borrador')
        product = ifactory.create(
            Product,
            name='Producto Zona',
            price=Decimal('50000.00'),
            is_active=True,
        )
        color = ifactory.create(Color, name='Negro', code='#000000')
        product_color = ifactory.create(
            ProductColor,
            product=product,
            color=color,
        )
        collection.products.add(product)
        collection.interactive_background = 'collections/interactive/test.png'
        collection.status = 'publicada'
        collection.save(update_fields=['interactive_background', 'status'])
        return collection, product, product_color
    return _create


@pytest.mark.django_db
class TestInteractiveZoneModel:
    def test_zone_valid_coordinates_saved(self, product_color_with_collection):
        collection, product, product_color = product_color_with_collection()

        zone = InteractiveZone(
            collection=collection,
            product_color=product_color,
            x=Decimal('10'),
            y=Decimal('20'),
            width=Decimal('30'),
            height=Decimal('25'),
        )
        zone.save()

        assert zone.pk is not None
        assert zone.collection == collection
        assert zone.product_color == product_color

    def test_zone_rejects_out_of_range_coordinates(self, product_color_with_collection):
        collection, product, product_color = product_color_with_collection()

        with pytest.raises(ValidationError):
            InteractiveZone(
                collection=collection,
                product_color=product_color,
                x=Decimal('150'),
                y=Decimal('20'),
                width=Decimal('30'),
                height=Decimal('25'),
            ).full_clean()

    def test_zone_rejects_overflow_beyond_image(self, product_color_with_collection):
        collection, product, product_color = product_color_with_collection()

        with pytest.raises(ValidationError):
            InteractiveZone(
                collection=collection,
                product_color=product_color,
                x=Decimal('90'),
                y=Decimal('90'),
                width=Decimal('30'),
                height=Decimal('25'),
            ).full_clean()

    def test_zone_rejects_zero_size(self, product_color_with_collection):
        collection, product, product_color = product_color_with_collection()

        with pytest.raises(ValidationError):
            InteractiveZone(
                collection=collection,
                product_color=product_color,
                x=Decimal('10'),
                y=Decimal('10'),
                width=Decimal('0'),
                height=Decimal('25'),
            ).full_clean()

    def test_zone_absolute_url_includes_color_param(self, product_color_with_collection):
        collection, product, product_color = product_color_with_collection()
        zone = InteractiveZone.objects.create(
            collection=collection,
            product_color=product_color,
            x=Decimal('10'),
            y=Decimal('20'),
            width=Decimal('30'),
            height=Decimal('25'),
        )

        assert str(product_color.pk) in zone.get_absolute_url()
        assert product.slug in zone.get_absolute_url()

    def test_zone_soft_delete_hides_from_default_manager(self, product_color_with_collection):
        collection, product, product_color = product_color_with_collection()
        zone = InteractiveZone.objects.create(
            collection=collection,
            product_color=product_color,
            x=Decimal('10'),
            y=Decimal('20'),
            width=Decimal('30'),
            height=Decimal('25'),
        )

        zone.soft_delete()

        assert InteractiveZone.objects.filter(pk=zone.pk).count() == 0
        assert InteractiveZone.all_objects.filter(pk=zone.pk).count() == 1


@pytest.mark.django_db
class TestCollectionInteractiveView:
    def test_public_view_renders_zones(self, client, product_color_with_collection):
        collection, product, product_color = product_color_with_collection()
        zone = InteractiveZone.objects.create(
            collection=collection,
            product_color=product_color,
            x=Decimal('10'),
            y=Decimal('20'),
            width=Decimal('30'),
            height=Decimal('25'),
        )

        url = reverse('products:collection_detail', kwargs={'slug': collection.slug})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert collection.interactive_background.url in content
        assert str(zone.x) in content
        assert product_color.pk is not None
        assert product.slug in content

    def test_public_view_404_without_interactive_background(self, client, ifactory):
        collection = ifactory.create(
            Collection,
            name='Colección Sin Fondo',
            slug='coleccion-sin-fondo',
            is_active=True,
            status='publicada',
        )

        url = reverse('products:collection_detail', kwargs={'slug': collection.slug})
        response = client.get(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestCollectionZoneEditorView:
    def test_editor_view_renders_with_zones(self, client, product_color_with_collection, ifactory):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = ifactory.create(User, username='editor', is_staff=True, is_superuser=True)
        client.force_login(user)

        collection, product, product_color = product_color_with_collection()
        InteractiveZone.objects.create(
            collection=collection,
            product_color=product_color,
            x=Decimal('10'),
            y=Decimal('10'),
            width=Decimal('20'),
            height=Decimal('20'),
        )

        url = reverse('products:collection_zones', kwargs={'pk': collection.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert 'zone-editor-data' in content
        assert 'interactive/test.png' in content
        assert collection.name in content

    def test_editor_view_requires_login(self, client, collection_with_interactive):
        collection = collection_with_interactive()

        url = reverse('products:collection_zones', kwargs={'pk': collection.pk})
        response = client.get(url)

        assert response.status_code in (302, 403)


@pytest.mark.django_db
class TestCollectionZoneAPI:
    def _login_staff(self, client, ifactory):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = ifactory.create(
            User,
            username='admin_zonas',
            is_staff=True,
            is_superuser=True,
        )
        user.set_password('pass1234')
        user.save()
        client.force_login(user)
        return user

    def test_api_creates_zone(self, client, product_color_with_collection, ifactory):
        collection, product, product_color = product_color_with_collection()
        self._login_staff(client, ifactory)

        url = reverse('products:collection_zones_api', kwargs={'pk': collection.pk})
        response = client.post(
            url,
            data={
                'x': 5, 'y': 5, 'width': 20, 'height': 15,
                'label': 'Zona central',
                'product_color_id': product_color.pk,
            },
            content_type='application/json',
        )

        assert response.status_code == 201
        assert response.json()['zone']['label'] == 'Zona central'
        assert InteractiveZone.objects.filter(collection=collection).count() == 1

    def test_api_rejects_product_not_in_collection(self, client, collection_with_interactive, ifactory):
        collection = collection_with_interactive()
        self._login_staff(client, ifactory)

        other_product = ifactory.create(
            Product,
            name='Otro Producto',
            price=Decimal('10000.00'),
            is_active=True,
        )
        other_color = ifactory.create(Color, name='Azul', code='#0000FF')
        other_pc = ifactory.create(ProductColor, product=other_product, color=other_color)

        url = reverse('products:collection_zones_api', kwargs={'pk': collection.pk})
        response = client.post(
            url,
            data={
                'x': 5, 'y': 5, 'width': 20, 'height': 15,
                'product_color_id': other_pc.pk,
            },
            content_type='application/json',
        )

        assert response.status_code == 400

    def test_api_rejects_invalid_coordinates(self, client, product_color_with_collection, ifactory):
        collection, product, product_color = product_color_with_collection()
        self._login_staff(client, ifactory)

        url = reverse('products:collection_zones_api', kwargs={'pk': collection.pk})
        response = client.post(
            url,
            data={
                'x': 200, 'y': 5, 'width': 20, 'height': 15,
                'product_color_id': product_color.pk,
            },
            content_type='application/json',
        )

        assert response.status_code == 400
        assert 'x' in response.json()['errors']

    def test_api_updates_zone(self, client, product_color_with_collection, ifactory):
        collection, product, product_color = product_color_with_collection()
        self._login_staff(client, ifactory)

        zone = InteractiveZone.objects.create(
            collection=collection,
            product_color=product_color,
            x=Decimal('10'),
            y=Decimal('10'),
            width=Decimal('20'),
            height=Decimal('20'),
        )

        url = reverse('products:collection_zone_api_detail', kwargs={'pk': collection.pk, 'zone_pk': zone.pk})
        response = client.put(
            url,
            data={
                'x': 30, 'y': 40, 'width': 25, 'height': 15,
                'label': 'Actualizada',
                'product_color_id': product_color.pk,
            },
            content_type='application/json',
        )

        assert response.status_code == 200
        zone.refresh_from_db()
        assert zone.x == Decimal('30.00')
        assert zone.y == Decimal('40.00')
        assert zone.label == 'Actualizada'

    def test_api_deletes_zone(self, client, product_color_with_collection, ifactory):
        collection, product, product_color = product_color_with_collection()
        self._login_staff(client, ifactory)

        zone = InteractiveZone.objects.create(
            collection=collection,
            product_color=product_color,
            x=Decimal('10'),
            y=Decimal('10'),
            width=Decimal('20'),
            height=Decimal('20'),
        )

        url = reverse('products:collection_zone_api_detail', kwargs={'pk': collection.pk, 'zone_pk': zone.pk})
        response = client.delete(url)

        assert response.status_code == 200
        assert response.json()['status'] == 'ok'
        assert InteractiveZone.all_objects.filter(pk=zone.pk).count() == 1
        assert InteractiveZone.objects.filter(pk=zone.pk).count() == 0
