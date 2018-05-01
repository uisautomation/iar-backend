import copy
import json
from unittest import mock
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from assets.models import Asset
from assets.tests.test_models import COMPLETE_ASSET
from assets.views import REQUIRED_SCOPES
from automationcommon.models import set_local_user
from automationlookup.models import UserLookup
from automationlookup.tests import set_cached_person_for_user

LOOKUP_RESPONSE = {
    'institutions': [{
        'url': 'http://lookupproxy:8080/institutions/TESTDEPT', 'acronym': None,
        'cancelled': False, 'instid': 'TESTDEPT', 'name': 'Test Department'
    }],
    'groups': [{
        'name': settings.IAR_USERS_LOOKUP_GROUP
    }],
}


class APIViewsTests(TestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.auth_patch = patch_authenticate()
        self.mock_authenticate = self.auth_patch.start()

        # By default, authentication succeeds
        self.user = get_user_model().objects.create_user(username="test0001")
        self.user_lookup = UserLookup.objects.create(
            user=self.user, scheme='mock', identifier=self.user.username)
        self.refresh_user()

        cache.set(f"{self.user.username}:lookup", LOOKUP_RESPONSE)

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
                                                 'id', 'allowed_methods'))

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
        self.assert_method_is_not_listed_as_allowed('PATCH', asset)
        self.assertEqual(result_patch.status_code, 403)

        # We fix the department, so now the user should be allow but we try to change the
        # department to another that the user doesn't belong to
        asset.department = 'TESTDEPT'
        set_local_user(self.user)
        asset.save()

        # User is in principle allowed ...
        self.assert_method_is_listed_as_allowed('PATCH', asset)

        # ... but not in this case
        result_patch = client.patch('/assets/%s/' % asset.pk, {"department": "TESTDEPT2"})
        self.assertEqual(result_patch.status_code, 403)

        # This one should be allowed
        result_patch = client.patch('/assets/%s/' % asset.pk, {"name": "asset2"})
        self.assert_method_is_listed_as_allowed('PATCH', asset)
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
        self.assert_method_is_not_listed_as_allowed('PUT', asset)
        self.assertEqual(result_put.status_code, 403)

        # We fix the department, so now the user should be allow but we try to change the
        # department to another that the user doesn't belong to
        asset.department = 'TESTDEPT'
        set_local_user(self.user)
        asset.save()

        # User can, in principle PUT...
        self.assert_method_is_listed_as_allowed('PUT', asset)

        # ... but not this asset
        result_put = client.put('/assets/%s/' % asset.pk, asset_dict)
        self.assertEqual(result_put.status_code, 403)

        # This one should be allowed
        asset_dict['department'] = 'TESTDEPT'
        asset_dict['name'] = 'asset2'
        result_put = client.put('/assets/%s/' % asset.pk, asset_dict)
        self.assert_method_is_listed_as_allowed('PUT', asset)
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

        cache.set(
            f"{self.user.username}:lookup",
            {
                **LOOKUP_RESPONSE,
                'institutions': [{**LOOKUP_RESPONSE['institutions'][0], 'instid': 'UIS'}]
            }
        )

        result_delete = client.delete(result_post.json()['url'])
        # User's institution doesn't match asset institution
        self.assert_method_is_not_listed_as_allowed('DELETE', asset)
        self.assertEqual(result_delete.status_code, 403)

        set_cached_person_for_user(self.user, LOOKUP_RESPONSE)
        self.assert_method_is_listed_as_allowed('DELETE', asset)

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

        cache.set(
            f"{self.user.username}:lookup",
            {
                **LOOKUP_RESPONSE,
                'institutions': [{**LOOKUP_RESPONSE['institutions'][0], 'instid': 'UIS'}]
            }
        )

        # DELETE not in allowed methods
        self.assert_method_is_not_listed_as_allowed('DELETE', asset)

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

        # DELETE is now in allowed methods
        self.assert_method_is_listed_as_allowed('DELETE', asset)

        result_delete = client.delete(result_post.json()['url'])
        self.assertEqual(result_delete.status_code, 204)

    def test_patch_with_perms(self):
        """A user with the change asset permission can patch an asset."""
        client = APIClient()
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['department'] = 'TESTDEPT2'
        asset = Asset(**asset_dict)
        asset.save()

        # PATCH not in allowed methods
        self.assert_method_is_not_listed_as_allowed('PATCH', asset)

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

        # PATCH is now in allowed methods
        self.assert_method_is_listed_as_allowed('PATCH', asset)

        result_patch = client.patch('/assets/%s/' % asset.pk, {"name": "asset1"})
        self.assertEqual(result_patch.status_code, 200)

    def test_put_with_perms(self):
        """A user with the change asset permission can put an asset."""
        client = APIClient()
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['department'] = 'TESTDEPT2'
        asset = Asset(**asset_dict)
        asset.save()

        # PUT not in allowed methods
        self.assert_method_is_not_listed_as_allowed('PUT', asset)

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

        # PUT is now in allowed methods
        self.assert_method_is_listed_as_allowed('PUT', asset)

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

    def test_iar_users_group_membership(self):
        """check that the user can do/see nothing if they aren't in uis-iar-users"""
        client = APIClient()

        # remove group membership
        cache.set(f"{self.user.username}:lookup", {**LOOKUP_RESPONSE, 'groups': []})

        # create a asset
        asset = Asset.objects.create(**COMPLETE_ASSET)
        asset_url = '/assets/%s/' % asset.pk

        # test no assets are listed
        self.assertEqual(client.get('/assets/', format='json').json()['results'], [])

        # test single asset isn't visible
        self.assertEqual(client.get(asset_url).status_code, 404)

        # test all change operations fail with 403
        self.assertEqual(client.post('/assets/', COMPLETE_ASSET, format='json').status_code, 403)
        self.assertEqual(client.put(asset_url, COMPLETE_ASSET, format='json').status_code, 403)
        self.assertEqual(client.patch(asset_url, {'name': 'new'}, format='json').status_code, 403)
        self.assertEqual(client.delete(asset_url).status_code, 403)

    def test_asset_stats(self):
        # test the asset stats end point
        client = APIClient()
        asset_dict1 = copy.copy(COMPLETE_ASSET)
        asset_dict2 = copy.copy(COMPLETE_ASSET)
        asset_dict3 = copy.copy(COMPLETE_ASSET)
        # asset2 incomplete and no personal data
        asset_dict2['personal_data'] = False
        del asset_dict2['name']
        self.assertEqual(client.post('/assets/', asset_dict1, format='json').status_code, 201)
        self.assertEqual(client.post('/assets/', asset_dict2, format='json').status_code, 201)
        cache.set(
            f"{self.user.username}:lookup",
            {
                **LOOKUP_RESPONSE,
                'institutions': [{**LOOKUP_RESPONSE['institutions'][0], 'instid': 'TESTDEPT2'}]
            }
        )
        asset_dict3['department'] = "TESTDEPT2"
        self.assertEqual(client.post('/assets/', asset_dict3, format='json').status_code, 201)
        response = client.get('/stats', format='json')
        self.assertDictEqual(json.loads(response.content), {
            'total_assets': 3,
            'total_assets_completed': 2,
            'total_assets_personal_data': 2,
            'total_assets_dept': [{'department': 'TESTDEPT', 'num_assets': 2},
                                  {'department': 'TESTDEPT2', 'num_assets': 1}],
            'total_assets_dept_completed': [{'department': 'TESTDEPT', 'num_assets': 1},
                                            {'department': 'TESTDEPT2', 'num_assets': 1}],
            'total_assets_dept_personal_data': [{'department': 'TESTDEPT', 'num_assets': 1},
                                                {'department': 'TESTDEPT2', 'num_assets': 1}],
        })

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

    def assert_method_is_listed_as_allowed(self, method, asset):
        """Assert that a given method appears in the allowed_methods list for an asset."""
        client = APIClient()
        result_get = client.get('/assets/%s/' % asset.pk)
        self.assertEqual(result_get.status_code, 200)
        self.assertIn(method, result_get.data['allowed_methods'])

    def assert_method_is_not_listed_as_allowed(self, method, asset):
        """Assert that a given method does not appear in the allowed_methods list for an asset."""
        client = APIClient()
        result_get = client.get('/assets/%s/' % asset.pk)
        self.assertEqual(result_get.status_code, 200)
        self.assertNotIn(method, result_get.data['allowed_methods'])

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
        self.user_lookup = UserLookup.objects.create(
            user=self.user, scheme='mock', identifier=self.user.username)

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
        'automationoauthdrf.authentication.OAuth2TokenAuthentication.authenticate',
        mock_authenticate
    )


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
