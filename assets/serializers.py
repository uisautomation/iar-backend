"""
Django REST framework serialisers.

"""
import contextlib

from rest_framework import serializers, fields
from rest_framework.exceptions import PermissionDenied

from assets.models import Asset


class AssetSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serialise a :py:class:`assets.models.Asset` object.

    If the request and view fields of the context are set then they are used to query the allowed
    methods on this object. These fields are set by the default get_serializer_context()
    implementation on ViewSets.

    """
    id = fields.UUIDField(format='hex_verbose', read_only=True)

    data_subject = fields.MultipleChoiceField(choices=Asset.DATA_SUBJECT_CHOICES,
                                              allow_null=True, allow_blank=True, required=False)
    data_category = fields.MultipleChoiceField(choices=Asset.DATA_CATEGORY_CHOICES,
                                               allow_null=True, allow_blank=True, required=False)
    risk_type = fields.MultipleChoiceField(choices=Asset.RISK_CHOICES, allow_null=True,
                                           allow_blank=True, required=False)
    storage_format = fields.MultipleChoiceField(choices=Asset.STORAGE_FORMAT_CHOICES,
                                                allow_null=True, allow_blank=True, required=False)
    paper_storage_security = fields.MultipleChoiceField(
        required=False, choices=Asset.PAPER_STORAGE_SECURITY_CHOICES, allow_null=True,
        allow_blank=True)
    digital_storage_security = fields.MultipleChoiceField(
        required=False, choices=Asset.DIGITAL_STORAGE_SECURITY_CHOICES, allow_null=True,
        allow_blank=True)
    is_complete = serializers.BooleanField(read_only=True)
    allowed_methods = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        exclude = ('deleted_at',)
        read_only_fields = ('created_at', 'updated_at', 'is_complete')

    def get_allowed_methods(self, obj):
        """
        Retrieve a list of allowed_methods the current user has on the object being serialised if
        the current request and view are present in the context.

        """
        # We need a request and view to return a result
        request = self.context.get('request')
        view = self.context.get('view')
        if request is None or view is None:
            return None

        allowed_methods = []
        for method in ['PUT', 'PATCH', 'DELETE']:
            with setting_request_method(request, method):
                try:
                    # We check all the permissions and append the method to the list of allowed
                    # methods. If we fail any permissions checks, then a PermissionDenied exception
                    # is thrown which we silently swallow.
                    view.check_permissions(request)
                    view.check_object_permissions(request, obj)
                    allowed_methods.append(method)
                except PermissionDenied:
                    pass

        return allowed_methods


class AssetDeptStatsSerializer(serializers.Serializer):
    """
    Asset Stats per Department serializer
    """
    department = serializers.CharField(help_text=(
        'Department code the asset belongs to'))
    num_assets = serializers.IntegerField(help_text=(
        'Number of assets hold by the department'))


class AssetCountsSerializer(serializers.Serializer):
    """
    Serialise a :py:class:`assets.views.AssetCounts` object.
    """
    total = serializers.IntegerField(help_text='Total number of asset entries')
    completed = serializers.IntegerField(help_text='Total number of completed asset entries')
    with_personal_data = serializers.IntegerField(
        help_text='Total number of asset entries for assets with personal data')


class AssetStatsSerializer(serializers.Serializer):
    """
    Serialise a :py:class:`assets.views.AssetStats` object.
    """
    all = AssetCountsSerializer(help_text='Statistics for all asset entries')
    by_institution = serializers.DictField(
        child=AssetCountsSerializer(),
        help_text='Statistics for asset entries grouped by Lookup instid')


@contextlib.contextmanager
def setting_request_method(request, method):
    """
    A context manager which temporarily changes the method of a request object. As a context
    manager, it guarantees that the method is reset to the original even if an exception is thrown.

    """
    original_method = request.method
    request.method = method
    yield request
    request.method = original_method
