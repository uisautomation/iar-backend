import copy
from django.test import TestCase
from assets.models import Asset


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


class AssetTests(TestCase):
    """
    Test's for the Asset model.
    """

    def test_is_complete(self):
        Asset.objects.create(**COMPLETE_ASSET)
        self.assertTrue(Asset.objects.first().is_complete)

    def test_is_complete_no_personal_data(self):
        # The asset doesn't contain personal data, so there is 3 fields that do not
        # need to be completed: data_subject, data_category, and retention
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['personal_data'] = False
        asset_dict['data_subject'] = []
        asset_dict['data_category'] = []
        del asset_dict['recipients_outside_uni']
        del asset_dict['recipients_outside_eea']
        del asset_dict['retention']
        Asset.objects.create(**asset_dict)
        self.assertTrue(Asset.objects.first().is_complete)

    def test_is_not_complete_name(self):
        """ Missing name so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['name']
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_purpose(self):
        """ Missing purpose so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['purpose']
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_owner(self):
        """ Missing owner when purpose='research' so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['owner']
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_purpose_other(self):
        """ Missing purpose_other when purpose='other' so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['purpose'] = 'other'
        del asset_dict['purpose_other']
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_data_subject(self):
        """ Missing data_subject when personal_data=True so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['data_subject'] = []
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_data_category(self):
        """ Missing data_category when personal_data=True so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['data_category'] = []
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_recipients_outside_uni(self):
        """ Missing recipients_outside_uni when personal_data=True so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['recipients_outside_uni']
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_recipients_outside_eea(self):
        """ Missing recipients_outside_eea when personal_data=True so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['recipients_outside_eea']
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_retention(self):
        """ Missing retention when personal_data=True so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['retention']
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_recipients_outside_uni_description(self):
        """
        Missing recipients_outside_uni_description when recipients_outside_uni=Yes
        so is_complete is False
        """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['recipients_outside_uni'] = 'yes'
        del asset_dict['recipients_outside_uni_description']
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_recipients_outside_eea_description(self):
        """
        Missing recipients_outside_eea_description when recipients_outside_eea=Yes
        so is_complete is False
        """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['recipients_outside_eea'] = 'yes'
        del asset_dict['recipients_outside_eea_description']
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_risk_type(self):
        """ Missing risk_type so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['risk_type'] = []
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_storage_location(self):
        """ Missing storage_location so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        del asset_dict['storage_location']
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_storage_format(self):
        """ Missing storage_format so is_complete is False """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['storage_format'] = []
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_paper_storage_security(self):
        """
        Missing paper_storage_security when storage_format contains 'paper'
        so is_complete is False
        """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['paper_storage_security'] = []
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)

    def test_is_not_complete_digital_storage_security(self):
        """
        Missing digital_storage_security when storage_format contains 'paper'
        so is_complete is False
        """
        asset_dict = copy.copy(COMPLETE_ASSET)
        asset_dict['digital_storage_security'] = []
        Asset.objects.create(**asset_dict)
        self.assertFalse(Asset.objects.first().is_complete)
