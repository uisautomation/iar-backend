from django.test import TestCase, override_settings


class StaticFQDNTest(TestCase):

    @override_settings(STATIC_URL='/static1/')
    def test_static_normal_file(self):
        response = self.client.get('/ui', follow=True)
        self.assertContains(response,
                            '"oauth2RedirectUrl": '
                            '"http://testserver/static1/iarbackend/oauth2-redirect.html"')

    @override_settings(STATIC_URL='https://foobar/static2/')
    def test_static_s3_file(self):
        response = self.client.get('/ui', follow=True)
        self.assertContains(
            response, '"oauth2RedirectUrl": '
                      '"https://foobar/static2/iarbackend/oauth2-redirect.html"')
