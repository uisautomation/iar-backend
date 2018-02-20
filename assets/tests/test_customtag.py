from django.conf import settings
from django.test import TestCase, override_settings
from assets.templatetags.oauth2file import oauth2file


class StaticFQDNTest(TestCase):

    @override_settings(STATIC_URL='/static1/')
    def test_static_normal_file(self):
        self.assertEqual(oauth2file("http", "testserver", "iarbackend/oauth2-redirect.html"),
                         "http://testserver/static1/iarbackend/oauth2-redirect.html")

    @override_settings(STATIC_URL='https://foobar/static2/')
    def test_static_s3_file(self):
        settings.STATIC_URL = 'https://foobar/static2/'
        self.assertEqual(
            oauth2file("http", "testserver", "iarbackend/oauth2-redirect.html"),
            "https://foobar/static2/iarbackend/oauth2-redirect.html")
