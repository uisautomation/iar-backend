from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from assets.models import Asset


class AdminViewsTests(TestCase):
    def setUp(self):
        super().setUp()
        self.asset = Asset.objects.create(name='foo')
        self.superuser = get_user_model().objects.create_user(
            username='testing', is_staff=True, is_superuser=True)

    def test_index(self):
        """Viewing the assets index in admin should be possible."""
        self.client.force_login(self.superuser)
        r = self.client.get(reverse('admin:assets_asset_changelist'))
        self.assertEqual(r.status_code, 200)
