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


COMPLETE_ASSET = {
    "data_subject": [
        "students"
    ],
    "data_category": [
        "research"
    ],
    "risk_type": [
        "operational", "reputational"
    ],
    "storage_format": [
        "digital", "paper"
    ],
    "paper_storage_security": [
        "locked_cabinet"
    ],
    "digital_storage_security": [
        "acl"
    ],
    "name": "asset1",
    "department": "TESTDEPT",
    "purpose": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
               "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis "
               "nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
               "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu "
               "fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
               "culpa qui officia deserunt mollit anim id est laborum.",
    "research": True,
    "owner": "amc203",
    "private": False,
    "personal_data": True,
    "recipients_category": "no idea",
    "recipients_outside_eea": "",
    "retention": "<1",
    "storage_location": "Who knows"
}


class APIViewsTests(TestCase):
    required_scopes = REQUIRED_SCOPES

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.auth_patch = self.patch_authenticate()
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

    def test_asset_post_is_complete(self):
        client = APIClient()
        result_post = client.post('/assets/', COMPLETE_ASSET, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(result_post.json()['url'], format='json')
        result_get_dict = result_get.json()
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['is_complete'] = True
        self.assert_dict_list_equal(asset_dict, result_get_dict,
                                    ignore_keys=('created_at', 'updated_at', 'url', 'id'))

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

    def test_asset_post_is_not_complete(self):
        client = APIClient()
        # Missing name thus is_complete should return False
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['name']
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(result_post.json()['url'], format='json')
        result_get_dict = result_get.json()
        asset_dict['is_complete'] = False
        asset_dict['name'] = None
        self.assert_dict_list_equal(asset_dict, result_get_dict,
                                    ignore_keys=('created_at', 'updated_at', 'url', 'id'))

    def test_asset_post_is_not_complete_risk(self):
        client = APIClient()
        # Missing risk_type thus is_complete should return False
        # This is an specific case because risk_type is a MultiSelect field, and these don't
        # have null values, only []
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['risk_type']
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(result_post.json()['url'], format='json')
        result_get_dict = result_get.json()
        asset_dict['is_complete'] = False
        asset_dict['risk_type'] = []
        self.assert_dict_list_equal(asset_dict, result_get_dict,
                                    ignore_keys=('created_at', 'updated_at', 'url', 'id'))

    def test_asset_post_is_complete_no_personal_data(self):
        client = APIClient()
        # The asset doesn't contain personal data, so there is 3 fields that do not
        # need to be completed: data_subject, data_category, and retention
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['personal_data'] = False
        del asset_dict['data_subject']
        del asset_dict['data_category']
        del asset_dict['retention']
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(result_post.json()['url'], format='json')
        result_get_dict = result_get.json()
        asset_dict['is_complete'] = True
        asset_dict['data_subject'] = []
        asset_dict['data_category'] = []
        asset_dict['retention'] = None
        self.assert_dict_list_equal(asset_dict, result_get_dict,
                                    ignore_keys=('created_at', 'updated_at', 'url', 'id'))

    def test_asset_post_missing_paper_storage_security(self):
        client = APIClient()
        # Missing paper_storage_security despite having paper on storage_format,
        # so returning not complete
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['paper_storage_security']
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(result_post.json()['url'], format='json')
        result_get_dict = result_get.json()
        asset_dict['is_complete'] = False
        asset_dict['paper_storage_security'] = []
        self.assert_dict_list_equal(asset_dict, result_get_dict,
                                    ignore_keys=('created_at', 'updated_at', 'url', 'id'))

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

    def test_field_filter(self):
        # Test that we can specify the value of a field and it will return those matching
        client = APIClient()
        asset_dict1 = copy.copy(COMPLETE_ASSET)
        asset_dict2 = copy.copy(COMPLETE_ASSET)
        asset_dict3 = copy.copy(COMPLETE_ASSET)
        asset_dict1['name'] = "asset"
        asset_dict2['name'] = "asset"
        asset_dict3['name'] = "asset3"
        self.assertEqual(client.post('/assets/', asset_dict2, format='json').status_code, 201)
        self.assertEqual(client.post('/assets/', asset_dict3, format='json').status_code, 201)
        self.assertEqual(client.post('/assets/', asset_dict1, format='json').status_code, 201)
        result_get = client.get('/assets/', data={'name': "asset"},
                                format='json')
        result_get_dict = result_get.json()
        self.assertTrue("results" in result_get_dict)
        self.assertEqual(len(result_get_dict["results"]), 2)
        result_get = client.get('/assets/', data={'name': "asset3"},
                                format='json')
        result_get_dict = result_get.json()
        self.assertTrue("results" in result_get_dict)
        self.assertEqual(len(result_get_dict["results"]), 1)
        self.assert_dict_list_equal(asset_dict3, result_get_dict["results"][0],
                                    ignore_keys=('created_at', 'updated_at', 'url', 'is_complete',
                                                 'id'))

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

    def patch_authenticate(self, return_value=None):
        """Patch authentication's authenticate function."""
        mock_authenticate = mock.MagicMock()
        mock_authenticate.return_value = return_value

        return mock.patch(
            'assets.authentication.OAuth2TokenAuthentication.authenticate', mock_authenticate)

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
        self.mock_authenticate.return_value = (self.user,
                                               {'scope': ' '.join(self.required_scopes)})


class SwaggerAPITest(TestCase):
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
