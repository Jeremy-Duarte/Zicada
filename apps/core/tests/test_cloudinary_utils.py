import pytest

from apps.core.cloudinary_utils import (
    build_cloudinary_url,
    build_image_url,
    build_transformation_string,
    get_default_image_url,
    get_srcset,
    get_thumbnail_url,
)


class TestCloudinaryUtils:
    def test_build_transformation_string_basic(self):
        result = build_transformation_string(width=600, height=400, crop='limit')
        assert result == 'w_600,h_400,c_limit'

    def test_build_transformation_string_with_extra(self):
        result = build_transformation_string(
            width=600, quality='auto', fetch_format='auto', dpr='auto',
        )
        assert 'w_600' in result
        assert 'q_auto' in result
        assert 'f_auto' in result
        assert 'dpr_auto' in result

    def test_build_cloudinary_url_adds_transformations(self):
        url = 'https://res.cloudinary.com/demo/image/upload/v1234/sample.jpg'
        result = build_cloudinary_url(url, width=600, quality='auto')
        assert 'w_600' in result
        assert 'q_auto' in result

    def test_build_cloudinary_url_no_upload_segment_returns_original(self):
        url = '/media/sample.jpg'
        result = build_cloudinary_url(url, width=600)
        assert result == url

    def test_build_cloudinary_url_empty_returns_empty(self):
        assert build_cloudinary_url('', width=600) == ''

    def test_build_image_url_includes_defaults(self):
        class MockField:
            url = 'https://res.cloudinary.com/demo/image/upload/v1234/sample.jpg'

        result = build_image_url(MockField(), width=800)
        assert 'w_800' in result
        assert 'f_auto' in result
        assert 'q_auto' in result
        assert 'dpr_auto' in result
        assert 'e_sharpen:400' in result

    def test_build_image_url_no_field_returns_empty(self):
        assert build_image_url(None) == ''
        assert build_image_url(object()) == ''

    def test_get_thumbnail_url(self):
        class MockField:
            url = 'https://res.cloudinary.com/demo/image/upload/v1234/sample.jpg'

        result = get_thumbnail_url(MockField(), width=200)
        assert 'w_200' in result
        assert 'h_200' in result
        assert 'c_fill' in result

    def test_get_srcset(self):
        class MockField:
            url = 'https://res.cloudinary.com/demo/image/upload/v1234/sample.jpg'

        result = get_srcset(MockField(), sizes=[400, 800])
        assert '400w' in result
        assert '800w' in result

    def test_get_default_image_url(self):
        class MockField:
            url = 'https://cloudinary.com/img.jpg'

        assert get_default_image_url(MockField()) == 'https://cloudinary.com/img.jpg'
        assert get_default_image_url(None) == ''
