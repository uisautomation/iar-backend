import copy
import json
from automationcommon.tests.utils import UnitTestCase
from rest_framework.test import APIClient


class APIViewsTests(UnitTestCase):
    def setUp(self):
        self.maxDiff = None

    def assertDictListEqual(self, odict1, odict2, ignore_keys=[], msg=None):
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
            del d1[k]
            del d2[k]
        for k, v in d1.items():
            if v.__class__ == list:
                d1[k] = set(v)
        for k, v in d2.items():
            if v.__class__ == list:
                d2[k] = set(v)
        return self.assertDictEqual(d1, d2, msg)

    def test_asset_post_is_complete(self):
        client = APIClient()
        asset_dict = {
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
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(json.loads(result_post.content)['url'], format='json')
        result_get_dict = json.loads(result_get.content)
        del result_get_dict['url']
        asset_dict['is_complete'] = True
        self.assertDictListEqual(asset_dict, result_get_dict, ignore_keys=['created_at', 'updated_at'])

    def test_asset_post_is_not_complete(self):
        client = APIClient()
        # Missing data_category_others but necessary as data_category include others,
        # thus is_complete should return False
        asset_dict = {
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
            "digital_storage_security": [
                "acl"
            ],
            "paper_storage_security": [
                "locked_cabinet"
            ],
            "department": "department test",
            "purpose": "don't know",
            "research": False,
            "private": True,
            "personal_data": False,
            "recipients_category": "no idea",
            "recipients_outside_eea": "",
            "retention": "<=1",
            "retention_other": "",
            "storage_location": "Who knows"
        }
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(json.loads(result_post.content)['url'], format='json')
        result_get_dict = json.loads(result_get.content)
        del result_get_dict['url']
        asset_dict['is_complete'] = False
        asset_dict['name'] = None
        asset_dict['owner'] = None
        self.assertDictListEqual(asset_dict, result_get_dict, ignore_keys=['created_at', 'updated_at'])

    def test_asset_post_missing_paper_storage_security_and_name(self):
        client = APIClient()
        # Missing paper_storage_security and name
        asset_dict = {
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
            "digital_storage_security": [
                "acl"
            ],
            "department": "department test",
            "purpose": "don't know",
            "owner": "amc203",
            "research": True,
            "private": True,
            "personal_data": False,
            "recipients_category": "no idea",
            "recipients_outside_eea": "",
            "retention": "<=1",
            "retention_other": "",
            "storage_location": "Who knows"
        }
        result_post = client.post('/assets/', asset_dict, format='json')
        self.assertEqual(result_post.status_code, 201)
        result_get = client.get(json.loads(result_post.content)['url'], format='json')
        result_get_dict = json.loads(result_get.content)
        del result_get_dict['url']
        asset_dict['is_complete'] = False
        asset_dict['name'] = None
        asset_dict['paper_storage_security'] = []
        self.assertDictListEqual(asset_dict, result_get_dict, ignore_keys=['created_at', 'updated_at'])
