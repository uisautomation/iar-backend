from rest_framework import serializers, fields
from assets.models import Asset


class AssetSerializer(serializers.HyperlinkedModelSerializer):
    data_subject = fields.MultipleChoiceField(choices=Asset.DATA_SUBJECT_CHOICES,
                                              allow_null=True, allow_blank=True, required=False)
    data_category = fields.MultipleChoiceField(choices=Asset.DATA_CATEGORY_CHOICES,
                                               allow_null=True, allow_blank=True, required=False)
    risk_type = fields.MultipleChoiceField(choices=Asset.RISK_CHOICES, allow_null=True,
                                           allow_blank=True, required=False)
    storage_format = fields.MultipleChoiceField(choices=Asset.STORAGE_FORMAT_CHOICES,
                                                allow_null=True, allow_blank=True, required=False)
    paper_storage_security = fields.MultipleChoiceField(required=False,
        choices=Asset.PAPER_STORAGE_SECURITY_CHOICES, allow_null=True, allow_blank=True)
    digital_storage_security = fields.MultipleChoiceField(required=False,
        choices=Asset.DIGITAL_STORAGE_SECURITY_CHOICES, allow_null=True, allow_blank=True)
    is_complete = serializers.BooleanField(read_only=True)
    class Meta:
        model = Asset
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
