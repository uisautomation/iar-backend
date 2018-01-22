from rest_framework import serializers, fields
from assets.models import Asset


class AssetSerializer(serializers.HyperlinkedModelSerializer):
    data_subject = fields.MultipleChoiceField(choices=Asset.DATA_SUBJECT_CHOICES)
    data_category = fields.MultipleChoiceField(choices=Asset.DATA_CATEGORY_CHOICES)
    risk_type = fields.MultipleChoiceField(choices=Asset.RISK_CHOICES)
    storage_format = fields.MultipleChoiceField(choices=Asset.STORAGE_FORMAT_CHOICES)
    paper_storage_security = fields.MultipleChoiceField(
        choices=Asset.PAPER_STORAGE_SECURITY_CHOICES)
    digital_storage_security = fields.MultipleChoiceField(
        choices=Asset.DIGITAL_STORAGE_SECURITY_CHOICES)
    class Meta:
        model = Asset
        fields = '__all__'
