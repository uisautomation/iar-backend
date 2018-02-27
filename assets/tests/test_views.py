import copy
from unittest import mock
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from assets.models import Asset
from assets.views import REQUIRED_SCOPES


# A complete asset used as a fixture in the following tests.
COMPLETE_ASSET = {
    "name": "asset1",
    "department": "TESTDEPT",
    "purpose": "research",
    "purpose_other": None,
    "owner": "amc203",
    "private": False,
    "personal_data": True,
    "data_subject": [
        "students"
    ],
    "data_category": [
        "research"
    ],
    "recipients_outside_uni": "yes",
    "recipients_outside_uni_description": "no idea",
    "recipients_outside_eea": "no",
    "recipients_outside_eea_description": None,
    "retention": "<1",
    "risk_type": [
        "operational", "reputational"
    ],
    "risk_type_additional": None,
    "storage_location": "Who knows",
    "storage_format": [
        "digital", "paper"
    ],
    "paper_storage_security": [
        "locked_cabinet"
    ],
    "digital_storage_security": [
        "acl"
    ],
}


class APIViewsTests(TestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.auth_patch = patch_authenticate()
        self.mock_authenticate = self.auth_patch.start()

        # By default, authentication succeeds
        self.user = get_user_model().objects.create_user(username="test0001")
        self.refresh_user()

        cache.set("%s:lookup" % self.user.username,
                  {'institutions': [{'url': 'http://lookupproxy:8080/institutions/TESTDEPT',
                                     'acronym': None, 'cancelled': False, 'instid': 'TESTDEPT',
                                     'name': 'Test Department'}]}, 120)

    def tearDown(self):
        self.auth_patch.stop()
        super().tearDown()

    def test_asset_post_auth(self):
        def request_cb():
            client = APIClient()
            return client.post('/assets/', COMPLETE_ASSET, format='json')
        self.assert_no_auth_fails(request_cb)
        self.assert_no_scope_fails(request_cb)

    def test_asset_post_validation(self):
        """User's only allow to post an asset that has a department their are part of"""
        client = APIClient()
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['department'] = 'TESTDEPT2'
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 403)

    def test_asset_post_id(self):
        """POST-ing a new asset gives it an id."""
        client = APIClient()
        result_post = client.post('/assets/', COMPLETE_ASSET, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(result_post.json()['url'], format='json')
        result_get_dict = result_get.json()
        self.assertIn('id', result_get_dict)
        self.assertIsNotNone(result_get_dict['id'])

    def test_asset_post_is_complete(self):
        self.assert_dict_list_equal(
            {**COMPLETE_ASSET, **{'is_complete': True}}, self.post_asset(COMPLETE_ASSET),
            ignore_keys=('created_at', 'updated_at', 'url', 'id')
        )

    def test_asset_post_is_complete_no_personal_data(self):
        # The asset doesn't contain personal data, so there is 3 fields that do not
        # need to be completed: data_subject, data_category, and retention
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['personal_data'] = False
        asset_dict['data_subject'] = []
        asset_dict['data_category'] = []
        del asset_dict['recipients_outside_uni']
        del asset_dict['recipients_outside_eea']
        del asset_dict['retention']
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': True}}, self.post_asset(asset_dict),
            ignore_keys=(
                'created_at', 'updated_at', 'url', 'id', 'data_subject', 'data_category',
                'recipients_outside_uni', 'recipients_outside_eea', 'retention'
            )
        )

    def test_asset_post_is_not_complete_name(self):
        """ Missing name so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['name']
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id', 'name')
        )

    def test_asset_post_is_not_complete_purpose(self):
        """ Missing purpose so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['purpose']
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id', 'purpose')
        )

    def test_asset_post_is_not_complete_owner(self):
        """ Missing owner when purpose='research' so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['owner']
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id', 'owner')
        )

    def test_asset_post_is_not_complete_purpose_other(self):
        """ Missing purpose_other when purpose='other' so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['purpose'] = 'other'
        del asset_dict['purpose_other']
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id', 'purpose_other')
        )

    def test_asset_post_is_not_complete_data_subject(self):
        """ Missing data_subject when personal_data=True so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['data_subject'] = []
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id')
        )

    def test_asset_post_is_not_complete_data_category(self):
        """ Missing data_category when personal_data=True so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['data_category'] = []
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id')
        )

    def test_asset_post_is_not_complete_recipients_outside_uni(self):
        """ Missing recipients_outside_uni when personal_data=True so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['recipients_outside_uni']
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id', 'recipients_outside_uni')
        )

    def test_asset_post_is_not_complete_recipients_outside_eea(self):
        """ Missing recipients_outside_eea when personal_data=True so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['recipients_outside_eea']
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id', 'recipients_outside_eea')
        )

    def test_asset_post_is_not_complete_retention(self):
        """ Missing retention when personal_data=True so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['retention']
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id', 'retention')
        )

    def test_asset_post_is_not_complete_recipients_outside_uni_description(self):
        """
        Missing recipients_outside_uni_description when recipients_outside_uni=Yes
        so is_complete is False
        """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['recipients_outside_uni'] = 'yes'
        del asset_dict['recipients_outside_uni_description']
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=(
                'created_at', 'updated_at', 'url', 'id', 'recipients_outside_uni_description'
            )
        )

    def test_asset_post_is_not_complete_recipients_outside_eea_description(self):
        """
        Missing recipients_outside_eea_description when recipients_outside_eea=Yes
        so is_complete is False
        """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['recipients_outside_eea'] = 'yes'
        del asset_dict['recipients_outside_eea_description']
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=(
                'created_at', 'updated_at', 'url', 'id', 'recipients_outside_eea_description'
            )
        )

    def test_asset_post_is_not_complete_risk_type(self):
        """ Missing risk_type so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['risk_type'] = []
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id')
        )

    def test_asset_post_is_not_complete_storage_location(self):
        """ Missing storage_location so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['storage_location']
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id', 'storage_location')
        )

    def test_asset_post_is_not_complete_storage_format(self):
        """ Missing storage_format so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['storage_format'] = []
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id')
        )

    def test_asset_post_is_not_complete_paper_storage_security(self):
        """
        Missing paper_storage_security when storage_format contains 'paper'
        so is_complete is False
        """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['paper_storage_security'] = []
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id')
        )

    def test_asset_post_is_not_complete_digital_storage_security(self):
        """
        Missing digital_storage_security when storage_format contains 'paper'
        so is_complete is False
        """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['digital_storage_security'] = []
        self.assert_dict_list_equal(
            {**asset_dict, **{'is_complete': False}}, self.post_asset(asset_dict),
            ignore_keys=('created_at', 'updated_at', 'url', 'id')
        )

    def test_search_filter(self):
        # Test that the search fields finds an asset called asset2 out of some assets
        client = APIClient()
        asset_dict1 = copy.copy(COMPLETE_ASSET)
        asset_dict2 = copy.copy(COMPLETE_ASSET)
        asset_dict3 = copy.copy(COMPLETE_ASSET)
        asset_dict1['name'] = "asset1"
        asset_dict2['name'] = "asset2"
        asset_dict3['name'] = "asset3"
        self.assertEqual(client.post('/assets/', asset_dict1, format='json').status_code, 201)
        result_post = client.post('/assets/', asset_dict2, format='json')
        self.assertEqual(result_post.status_code, 201)
        self.assertEqual(client.post('/assets/', asset_dict3, format='json').status_code, 201)
        result_get = client.get('/assets/', data={'search': "asset2"},
                                format='json')
        result_get_dict = result_get.json()
        self.assertTrue("results" in result_get_dict)
        self.assertEqual(len(result_get_dict["results"]), 1)
        self.assert_dict_list_equal(asset_dict2, result_get_dict["results"][0],
                                    ignore_keys=('created_at', 'updated_at', 'url', 'is_complete',
                                                 'id'))

    def test_order_filter(self):
        # test that we can order the list of all assets by name (asc, desc)
        client = APIClient()
        asset_dict1 = copy.copy(COMPLETE_ASSET)
        asset_dict2 = copy.copy(COMPLETE_ASSET)
        asset_dict3 = copy.copy(COMPLETE_ASSET)
        asset_dict1['name'] = "asset1"
        asset_dict2['name'] = "asset2"
        asset_dict3['name'] = "asset3"
        self.assertEqual(client.post('/assets/', asset_dict2, format='json').status_code, 201)
        self.assertEqual(client.post('/assets/', asset_dict3, format='json').status_code, 201)
        self.assertEqual(client.post('/assets/', asset_dict1, format='json').status_code, 201)
        result_get = client.get('/assets/', data={'ordering': "name"},
                                format='json')
        result_get_dict = result_get.json()
        self.assertTrue("results" in result_get_dict)
        self.assertEqual(len(result_get_dict["results"]), 3)
        self.assertEqual(result_get_dict["results"][0]["name"], "asset1")
        self.assertEqual(result_get_dict["results"][1]["name"], "asset2")
        self.assertEqual(result_get_dict["results"][2]["name"], "asset3")

        result_get = client.get('/assets/', data={'ordering': "-name"},
                                format='json')
        result_get_dict = result_get.json()
        self.assertTrue("results" in result_get_dict)
        self.assertEqual(len(result_get_dict["results"]), 3)
        self.assertEqual(result_get_dict["results"][0]["name"], "asset3")
        self.assertEqual(result_get_dict["results"][1]["name"], "asset2")
        self.assertEqual(result_get_dict["results"][2]["name"], "asset1")

    def test_is_complete_on_put(self):
        """Test that is_complete is refreshed on an update"""
        client = APIClient()
        asset_dict1 = copy.copy(COMPLETE_ASSET)
        del asset_dict1['name']
        result_post = client.post('/assets/', asset_dict1, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(result_post.json()['url'], format='json')
        self.assertFalse(result_get.json()["is_complete"])
        result_put = client.put(result_post.json()['url'], COMPLETE_ASSET)
        self.assertTrue(result_put.json()["is_complete"])

    def test_is_complete_on_patch(self):
        """Test that is_complete is refreshed on an update"""
        client = APIClient()
        asset_dict1 = copy.copy(COMPLETE_ASSET)
        del asset_dict1['name']
        result_post = client.post('/assets/', asset_dict1, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(result_post.json()['url'], format='json')
        self.assertFalse(result_get.json()["is_complete"])
        result_patch = client.patch(result_post.json()['url'], {"name": "asset1"})
        self.assertTrue(result_patch.json()["is_complete"])

    def test_asset_patch_validation(self):
        """User's only allow to PATCH an asset that has a department their are part of, and the
        PATCH department has to be one he belongs to"""
        client = APIClient()
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['department'] = 'TESTDEPT2'
        asset = Asset(**asset_dict)
        asset.save()
        result_patch = client.patch('/assets/%s/' % asset.pk, {"name": "asset1"})
        # Not allowed because the asset belongs to TESTDEPT2
        self.assertEqual(result_patch.status_code, 403)

        # We fix the department, so now the user should be allow but we try to change the
        # department to another that the user doesn't belong to
        asset.department = 'TESTDEPT'
        asset.save()
        result_patch = client.patch('/assets/%s/' % asset.pk, {"department": "TESTDEPT2"})
        self.assertEqual(result_patch.status_code, 403)

        # This one should be allowed
        result_patch = client.patch('/assets/%s/' % asset.pk, {"name": "asset2"})
        self.assertEqual(result_patch.status_code, 200)

    def test_asset_put_validation(self):
        """User's only allow to PUT an asset that has a department their are part of, and the
        PUT department has to be one he belongs to"""
        client = APIClient()
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['department'] = 'TESTDEPT2'
        asset = Asset(**asset_dict)
        asset.save()
        result_put = client.put('/assets/%s/' % asset.pk, COMPLETE_ASSET)
        # Not allowed because the asset belongs to TESTDEPT2
        self.assertEqual(result_put.status_code, 403)

        # We fix the department, so now the user should be allow but we try to change the
        # department to another that the user doesn't belong to
        asset.department = 'TESTDEPT'
        asset.save()
        result_put = client.put('/assets/%s/' % asset.pk, asset_dict)
        self.assertEqual(result_put.status_code, 403)

        # This one should be allowed
        asset_dict['department'] = 'TESTDEPT'
        asset_dict['name'] = 'asset2'
        result_put = client.put('/assets/%s/' % asset.pk, asset_dict)
        self.assertEqual(result_put.status_code, 200)

    def test_privacy(self):
        """Test that a User cannot see/access to assets that are private outside their
        department"""
        client = APIClient()
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['department'] = 'TESTDEPT2'
        asset_dict['private'] = True
        asset = Asset(**asset_dict)
        asset.save()
        result_patch = client.get('/assets/%s/' % asset.pk)
        self.assertEqual(result_patch.status_code, 404)
        list_assets = client.get('/assets/', format='json')
        self.assertEqual(list_assets.json()['results'], [])

    def test_delete(self):
        """Test that the asset is not deleted but marked as deleted"""
        client = APIClient()
        asset_dict1 = copy.copy(COMPLETE_ASSET)
        result_post = client.post('/assets/', asset_dict1, format='json')
        self.assertEqual(result_post.status_code, 201)
        asset = Asset.objects.get(pk=result_post.json()['id'])
        self.assertIsNone(asset.deleted_at)

        # Check that there is 1 asset listed
        list_assets = client.get('/assets/', format='json')
        self.assertNotEqual(list_assets.json()['results'], [])

        cache.set("%s:lookup" % self.user.username,
                  {'institutions': [{'url': 'http://lookupproxy:8080/institutions/UIS',
                                     'acronym': None, 'cancelled': False, 'instid': 'UIS',
                                     'name': 'University Information Services'}]}, 120)

        result_delete = client.delete(result_post.json()['url'])
        # User's institution doesn't match asset institution
        self.assertEqual(result_delete.status_code, 403)

        cache.delete("%s:lookup" % self.user.username)
        cache.set("%s:lookup" % self.user.username,
                  {'institutions': [{'url': 'http://lookupproxy:8080/institutions/TESTDEPT',
                                     'acronym': None, 'cancelled': False, 'instid': 'TESTDEPT',
                                     'name': 'Test Department'}]}, 120)
        result_delete = client.delete(result_post.json()['url'])
        # User's institution match asset institution
        self.assertEqual(result_delete.status_code, 204)
        asset.refresh_from_db()
        self.assertIsNotNone(asset.deleted_at)

        # Check that no assets are listed
        list_assets = client.get('/assets/', format='json')
        self.assertEqual(list_assets.json()['results'], [])

        # Check that you can't retrieve an asset
        asset_get = client.get(result_post.json()['url'], format='json')
        self.assertEqual(asset_get.status_code, 404)

    def test_delete_with_perms(self):
        """Super users can delete any asset,"""
        client = APIClient()
        asset_dict1 = copy.copy(COMPLETE_ASSET)
        result_post = client.post('/assets/', asset_dict1, format='json')
        self.assertEqual(result_post.status_code, 201)
        asset = Asset.objects.get(pk=result_post.json()['id'])
        self.assertIsNone(asset.deleted_at)

        cache.set("%s:lookup" % self.user.username,
                  {'institutions': [{'url': 'http://lookupproxy:8080/institutions/UIS',
                                     'acronym': None, 'cancelled': False, 'instid': 'UIS',
                                     'name': 'University Information Services'}]}, 120)

        # Initially fails
        result_delete = client.delete(result_post.json()['url'])
        self.assertEqual(result_delete.status_code, 403)

        # Succeeds if use has permission
        perm = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Asset), codename='delete_asset')
        self.user.user_permissions.add(perm)
        self.user.save()

        self.refresh_user()

        self.assertTrue(self.user.has_perm('assets.delete_asset'))
        result_delete = client.delete(result_post.json()['url'])
        self.assertEqual(result_delete.status_code, 204)

    def test_patch_with_perms(self):
        """A user with the change asset permission can patch an asset."""
        client = APIClient()
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['department'] = 'TESTDEPT2'
        asset = Asset(**asset_dict)
        asset.save()

        result_patch = client.patch('/assets/%s/' % asset.pk, {"name": "asset1"})

        # Not allowed because the asset belongs to TESTDEPT2
        self.assertEqual(result_patch.status_code, 403)

        # Succeeds if use has permission
        perm = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Asset), codename='change_asset')
        self.user.user_permissions.add(perm)
        self.user.save()

        self.refresh_user()

        self.assertTrue(self.user.has_perm('assets.change_asset'))
        result_patch = client.patch('/assets/%s/' % asset.pk, {"name": "asset1"})
        self.assertEqual(result_patch.status_code, 200)

    def test_put_with_perms(self):
        """A user with the change asset permission can put an asset."""
        client = APIClient()
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['department'] = 'TESTDEPT2'
        asset = Asset(**asset_dict)
        asset.save()
        result_put = client.put('/assets/%s/' % asset.pk, COMPLETE_ASSET)

        # Not allowed because the asset belongs to TESTDEPT2
        self.assertEqual(result_put.status_code, 403)

        # Succeeds if use has permission
        perm = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Asset), codename='change_asset')
        self.user.user_permissions.add(perm)
        self.user.save()

        self.refresh_user()

        self.assertTrue(self.user.has_perm('assets.change_asset'))
        result_put = client.put('/assets/%s/' % asset.pk, COMPLETE_ASSET)
        self.assertEqual(result_put.status_code, 200)

    def test_post_with_perms(self):
        """A user with the create asset permission can post an asset."""
        client = APIClient()
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['department'] = 'TESTDEPT2'
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 403)

        # Succeeds if use has permission
        perm = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Asset), codename='add_asset')
        self.user.user_permissions.add(perm)
        self.user.save()

        self.refresh_user()

        self.assertTrue(self.user.has_perm('assets.add_asset'))
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 201)

    def refresh_user(self):
        """Refresh user from the database."""
        self.user = get_user_model().objects.get(pk=self.user.pk)
        self.mock_authenticate.return_value = (self.user, {'scope': ' '.join(REQUIRED_SCOPES)})

    def assert_no_auth_fails(self, request_cb):
        """Passing no authorisation fails."""
        self.mock_authenticate.return_value = None
        self.assertEqual(request_cb().status_code, 401)

    def assert_no_scope_fails(self, request_cb):
        """Passing authorisation with incorrect scopes fail."""
        self.mock_authenticate.return_value = (None, {'scope': 'not right'})
        self.assertEqual(request_cb().status_code, 403)

    def assert_dict_list_equal(self, odict1, odict2, ignore_keys=(), msg=None):
        """
        :param odict1: dictionary 1 that you want to compare to dictionary 2
        :param odict2: dictionary 2 that you want to compare to dictionary 1
        :param ignore_keys: list of the dictionary keys you don't want to compare
        :param msg: pass statement - shown on failure
        :type odict1: dict
        :type odict2: dict
        :type ignore_keys: list
        Compares two dictionary with lists (ignoring the order of the lists).
        """
        d1 = copy.copy(odict1)
        d2 = copy.copy(odict2)
        for k in ignore_keys:
            d1.pop(k, None)
            d2.pop(k, None)
        for k, v in d1.items():
            if v.__class__ == list:
                d1[k] = set(v)
        for k, v in d2.items():
            if v.__class__ == list:
                d2[k] = set(v)
        return self.assertDictEqual(d1, d2, msg)

    def post_asset(self, asset):
        """Helper for creating an asset and parsing the response"""
        client = APIClient()
        result_post = client.post('/assets/', asset, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(result_post.json()['url'], format='json')
        return result_get.json()


# An alternate asset to COMPLETE_ASSET. It is intended the this asset is never filtered for in
# AssetFilterTests.
DIFFERENT_ASSET = {
    "name": "asset2",
    "department": "OTHER",
    "purpose": "other",
    "purpose_other": "Something else",
    "owner": None,
    "private": True,
    "personal_data": False,
    "data_subject": [],
    "data_category": [],
    "recipients_outside_uni": None,
    "recipients_outside_uni_description": None,
    "recipients_outside_eea": None,
    "recipients_outside_eea_description": None,
    "retention": None,
    "risk_type": [
        "operational", "reputational"
    ],
    "risk_type_additional": None,
    "storage_location": "Who knows",
    "storage_format": [
        "digital", "paper"
    ],
    "paper_storage_security": [
        "locked_cabinet"
    ],
    "digital_storage_security": [
        "acl"
    ],
}


class AssetFilterTests(TestCase):
    """
    Tests relating to the custom DjangoFilterBackend filter_class -> AssetFilter
    """
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.auth_patch = patch_authenticate()
        self.mock_authenticate = self.auth_patch.start()

        # By default, authentication succeeds
        self.user = get_user_model().objects.create_user(username="test0001")
        self.mock_authenticate.return_value = (self.user, {'scope': ' '.join(REQUIRED_SCOPES)})

        self.client = APIClient()
        self.client.post('/assets/', COMPLETE_ASSET, format='json')
        self.client.post('/assets/', DIFFERENT_ASSET, format='json')

    def test_filter_by_department(self):
        self.assertAsset1(
            self.client.get('/assets/', data={'department': 'TESTDEPT'}, format='json')
        )

    def test_filter_by_purpose(self):
        self.assertAsset1(
            self.client.get('/assets/', data={'purpose': 'research'}, format='json')
        )

    def test_filter_by_owner(self):
        self.assertAsset1(
            self.client.get('/assets/', data={'owner': 'amc203'}, format='json')
        )

    def test_filter_by_private(self):
        self.assertAsset1(
            self.client.get('/assets/', data={'private': 'false'}, format='json')
        )

    def test_filter_by_personal_data(self):
        self.assertAsset1(
            self.client.get('/assets/', data={'personal_data': 'true'}, format='json')
        )

    def test_filter_by_recipients_outside_uni(self):
        self.assertAsset1(
            self.client.get('/assets/', data={'recipients_outside_uni': 'yes'}, format='json')
        )

    def test_filter_by_recipients_outside_eea(self):
        self.assertAsset1(
            self.client.get('/assets/', data={'recipients_outside_eea': 'no'}, format='json')
        )

    def test_filter_by_retention(self):
        self.assertAsset1(
            self.client.get('/assets/', data={'retention': '<1'}, format='json')
        )

    def test_filter_is_complete(self):
        self.assertAsset1(
            self.client.get('/assets/', data={'is_complete': 'true'}, format='json')
        )

    def tearDown(self):
        self.auth_patch.stop()
        super().tearDown()

    def assertAsset1(self, results):
        """
        Assert that only the result set contains exactly the COMPLETE_ASSET.
        :param results: test Assets result set.
        """
        result_get_dict = results.json()
        self.assertTrue("results" in result_get_dict)
        self.assertEqual(len(result_get_dict['results']), 1)
        self.assertEqual(result_get_dict['results'][0]['name'], 'asset1')


def patch_authenticate(return_value=None):
    """Patch authentication's authenticate function."""
    mock_authenticate = mock.MagicMock()
    mock_authenticate.return_value = return_value

    return mock.patch(
        'assets.authentication.OAuth2TokenAuthentication.authenticate', mock_authenticate)


class SwaggerAPITest(TestCase):
    """
    Tests relating to the use of Swagger (OpenAPI)
    """
    def test_security_definitions(self):
        """API spec should define an oauth2 security requirement."""
        spec = self.get_spec()
        self.assertIn('securityDefinitions', spec)
        self.assertIn('oauth2', spec['securityDefinitions'])

    def get_spec(self):
        """Return the Swagger (OpenAPI) spec as parsed JSON."""
        client = APIClient()
        response = client.get(reverse('schema-json', kwargs={'format': '.json'}))
        self.assertEqual(response.status_code, 200)
        return response.json()
