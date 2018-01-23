import json
from automationcommon.tests.utils import UnitTestCase
from rest_framework.test import APIClient


class APIViewsTests(UnitTestCase):
    def setUp(self):
        self.maxDiff = None

    def test_asset_post_is_complete(self):
        client = APIClient()
        asset_dict = {
            "data_subject": [
                "students"
            ],
            "data_category": [
                "personal", "research"
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
            "owner": "amc203",
            "private": True,
            "personal_data": False,
            "data_category_others": "",
            "recipients_category": "no idea",
            "recipients_outside_eea": False,
            "recipients_outside_eea_who": "",
            "retention": "<=1",
            "retention_other": "",
            "storage_location": "Who knows"
        }

        result_post = client.post('/assets/', asset_dict, format='json')
        result_get = client.get(json.loads(result_post.content)['url'], format='json')
        result_get_dict = json.loads(result_get.content)
        del result_get_dict['url']
        asset_dict['is_complete'] = True
        for k, v in asset_dict.items():
            if v.__class__ == list:
                asset_dict[k] = set(v)
        for k, v in result_get_dict.items():
            if v.__class__ == list:
                result_get_dict[k] = set(v)
        self.assertDictEqual(asset_dict, result_get_dict)
