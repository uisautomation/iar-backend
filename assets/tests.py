from automationcommon.tests.utils import UnitTestCase
from django.test import TestCase
from rest_framework.test import APIClient


class APIViewsTests(UnitTestCase):

    def test_asset_post(self):
        client = APIClient()
        asset_json = {
            "data_subject": [
                "students"
            ],
            "data_category": [
                "personal",
                "research"
            ],
            "risk_type": [
                "operational",
                "reputational"
            ],
            "storage_format": [
                "digital"
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

        result_post = client.post('/assets/', asset_json, format='json')
        result_get = client.get(result_post['url'], format='json')
        self.assertEqual(asset_json, result_get)
