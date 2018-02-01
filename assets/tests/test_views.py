import copy
import json
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

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
    "department": "department test",
    "purpose": "don't know",
    "research": True,
    "owner": "amc203",
    "private": True,
    "personal_data": False,
    "recipients_category": "no idea",
    "recipients_outside_eea": "",
    "retention": "<=1",
    "retention_other": "",
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
        self.mock_authenticate.return_value = (None, {'scope': ' '.join(self.required_scopes)})

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
        result_get = client.get(json.loads(result_post.content)['url'], format='json')
        result_get_dict = json.loads(result_get.content)
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['is_complete'] = True
        self.assert_dict_list_equal(asset_dict, result_get_dict,
                                    ignore_keys=('created_at', 'updated_at', 'url'))

    def test_asset_post_is_not_complete(self):
        client = APIClient()
        # Missing name thus is_complete should return False
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['name']
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(json.loads(result_post.content)['url'], format='json')
        result_get_dict = json.loads(result_get.content)
        asset_dict['is_complete'] = False
        asset_dict['name'] = None
        self.assert_dict_list_equal(asset_dict, result_get_dict,
                                    ignore_keys=('created_at', 'updated_at', 'url'))

    def test_asset_post_missing_paper_storage_security(self):
        client = APIClient()
        # Missing paper_storage_security despite having paper on storage_format,
        # so returning not complete
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['paper_storage_security']
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(json.loads(result_post.content)['url'], format='json')
        result_get_dict = json.loads(result_get.content)
        asset_dict['is_complete'] = False
        asset_dict['paper_storage_security'] = []
        self.assert_dict_list_equal(asset_dict, result_get_dict,
                                    ignore_keys=('created_at', 'updated_at', 'url'))

    def assert_no_auth_fails(self, request_cb):
        """Passing no authorisation fails."""
        self.mock_authenticate.return_value = None
        self.assertEqual(request_cb().status_code, 403)

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
