from automationcommon.models import Audit, set_local_user, clear_local_user
from django.contrib.auth import get_user_model
from django.test import TestCase

from assets.models import Asset, UserLookup


class AuditTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test0001')
        self.user_lookup = UserLookup.objects.create(
            user=self.user, scheme='mock', identifier=self.user.username)
        set_local_user(self.user)
        self.asset = Asset(name='test-asset')
        self.asset.save()

    def tearDown(self):
        clear_local_user()

    def test_no_audits_initially(self):
        """With no changes, there should be no audit."""
        self.assertEqual(Audit.objects.count(), 0)

    def test_create(self):
        """Changing an asset makes an audit record."""
        old_name = self.asset.name
        self.asset.name = 'new-name'
        self.asset.save()
        self.assertEqual(Audit.objects.count(), 1)
        audit = Audit.objects.filter(model_pk=repr(self.asset.pk)).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.field, 'name')
        self.assertEqual(audit.old, old_name)
        self.assertEqual(audit.new, self.asset.name)
        self.assertEqual(audit.who.pk, self.user.pk)
