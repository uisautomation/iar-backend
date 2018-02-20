from django.test import TestCase


class HasScopesTest(TestCase):
    def test_static_file(self):
        with self.settings(STATIC_URL='/static1/'):
            response = self.client.get('/ui', follow=True)
            import sys
            sys.stdout.write(str(response.content))
            self.assertContains(response,
                                '"oauth2RedirectUrl": "/static1/iarbackend/oauth2-redirect.html"')
        with self.settings(STATIC_URL='https://foobar/static2/'):
            response = self.client.get('/ui', follow=True)
            self.assertContains(
                response,
                '"oauth2RedirectUrl": "https://foobar/static2/iarbackend/oauth2-redirect.html"')
