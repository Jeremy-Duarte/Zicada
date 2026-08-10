import pytest

from apps.core.cloudinary_utils import (
    build_cloudinary_url,
    build_transformation_string,
    is_cloudinary_url,
    parse_cloudinary_public_id,
)


class TestCloudinaryUtils:
    def test_is_cloudinary_url_with_cloudinary(self):
        url = 'https://res.cloudinary.com/demo/image/upload/v1234/sample.jpg'
        assert is_cloudinary_url(url) is True

    def test_is_cloudinary_url_with_local(self):
        url = '/media/sample.jpg'
        assert is_cloudinary_url(url) is False

    def test_build_transformation_string(self):
        result = build_transformation_string(width=600, height=400, crop='limit')
        assert result == 'w_600,h_400,c_limit,q_auto,f_auto'

    def test_build_cloudinary_url_adds_transformations(self):
        url = 'https://res.cloudinary.com/demo/image/upload/v1234/sample.jpg'
        result = build_cloudinary_url(url, width=600)
        assert 'w_600' in result
        assert 'q_auto' in result
        assert 'f_auto' in result

    def test_build_cloudinary_url_ignores_non_cloudinary(self):
        url = '/media/sample.jpg'
        result = build_cloudinary_url(url, width=600)
        assert result == url

    def test_parse_cloudinary_public_id(self):
        url = 'https://res.cloudinary.com/demo/image/upload/v1234/sample.jpg'
        assert parse_cloudinary_public_id(url) == 'sample'
