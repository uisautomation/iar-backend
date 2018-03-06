"""
Views for the assets application.
"""
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response

from automationcommon.models import set_local_user, clear_local_user

from django.core.cache import cache
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django_filters.rest_framework import (
    DjangoFilterBackend, FilterSet, CharFilter, BooleanFilter, ChoiceFilter
)
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter

from iarbackend.settings import IAR_USERS_LOOKUP_GROUP
from .authentication import OAuth2TokenAuthentication
from .models import Asset
from .permissions import HasScopesPermission, UserInInstitutionPermission, OrPermission, AndPermission, \
    UserInIARGroupPermission
from .serializers import AssetSerializer


# Scopes required to access asset register.
REQUIRED_SCOPES = ['assetregister']


"""
List of OAuth2 scopes required by this client.

"""


SCHEMA_DECORATOR = swagger_auto_schema(operation_security=[{'oauth2': REQUIRED_SCOPES}])
"""
Decorator to apply to DRF methods which sets the appropriate security requirements.

"""


class AssetFilter(FilterSet):
    """
    A custom DjangoFilterBackend filter_class defining all filterable fields.
    It seems that simply using filter_fields doesn't work with the is_complete fields.

    This class was implemented using the example here:
    https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html#adding-a-filterset-with-filter-class
    """
    department = CharFilter(name="department")
    purpose = ChoiceFilter(choices=Asset.PURPOSE_CHOICES)
    owner = CharFilter(name="owner")
    private = BooleanFilter(name="private")
    personal_data = BooleanFilter(name="personal_data")
    recipients_outside_uni = ChoiceFilter(choices=Asset.RECIPIENTS_OUTSIDE_CHOICES)
    recipients_outside_eea = ChoiceFilter(choices=Asset.RECIPIENTS_OUTSIDE_CHOICES)
    retention = ChoiceFilter(choices=Asset.RETENTION_CHOICES)
    is_complete = BooleanFilter(name="is_complete")
    # TODO:
    # It seem's probable that we would like to filter on the follow list ofMultiSelectField fields.
    # However, we should implement this when we know how we would like to filter them.
    #   data_subject,
    #   data_category,
    #   risk_type,
    #   storage_format,
    #   paper_storage_security,
    #   digital_storage_security

    class Meta:
        model = Asset
        fields = [
            'department', 'purpose', 'owner', 'private', 'personal_data', 'recipients_outside_eea',
            'recipients_outside_uni', 'is_complete', 'retention'
        ]


@method_decorator(name='create', decorator=SCHEMA_DECORATOR)
@method_decorator(name='retrieve', decorator=SCHEMA_DECORATOR)
@method_decorator(name='update', decorator=SCHEMA_DECORATOR)
@method_decorator(name='partial_update', decorator=SCHEMA_DECORATOR)
@method_decorator(name='destroy', decorator=SCHEMA_DECORATOR)
@method_decorator(name='list', decorator=SCHEMA_DECORATOR)
class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows assets to be created, viewed, searched, filtered, and ordered
    by any field.

    To order by a specific field you need to include in your GET request a parameter called
    ordering with the name of the field you want to order by. You can also order in reverse
    by adding the character "-" at the beginning of the name of the field.

    You can also use the parameter search in your request with the text that you want to search.
    This text will be searched on all fields and will return all possible results

    You can also filter by a specific field. For example if you only want to return those assets
    with name "foobar" you can add to your GET request a parameter called name (name of the field)
    and the value you want to filter by. Example ?name=foobar (this will return all assets
    that have as name "foobar").

    """
    queryset = Asset.objects.filter(deleted_at__isnull=True)
    serializer_class = AssetSerializer

    ordering = ('-created_at',)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_class = AssetFilter
    search_fields = (
        'name', 'purpose_other',
        'recipients_outside_uni_description',
        'recipients_outside_eea_description',
        'risk_type_additional', 'storage_location',
        # TODO
        # a search on the following fields won't work as the user would probably expect as they
        # store a mnemonic and not the text that the user sees.
        'department', 'purpose', 'owner', 'data_subject', 'data_category', 'retention',
        'risk_type', 'storage_format', 'paper_storage_security', 'digital_storage_security',
    )
    ordering_fields = search_fields + (
        'id', 'private', 'personal_data', 'recipients_outside_uni', 'recipients_outside_eea',
        'created_at', 'updated_at', 'is_complete'
    )

    authentication_classes = (OAuth2TokenAuthentication,)
    required_scopes = REQUIRED_SCOPES

    permission_classes = (
        HasScopesPermission, OrPermission(
            DjangoModelPermissions, AndPermission(
                UserInIARGroupPermission, UserInInstitutionPermission
            )
        )
    )

    def initial(self, request, *args, **kwargs):
        """Runs anything that needs to occur prior to calling the method handler."""
        # Perform any authentication, permissions checking etc.
        super().initial(request, *args, **kwargs)

        # Set the local user for the auditing framework
        set_local_user(request.user)

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Returns the final response object.
        """
        # By this time the local user has been recorded if necessary.
        clear_local_user()

        return super().finalize_response(request, response, *args, **kwargs)

    def get_queryset(self):
        """get_queryset is patched to only return those assets that are not private or that are
        prive but the user doing the request belongs to department that owns the asset."""

        lookup_response = cache.get(
            f"{self.request.user.username}:lookup", {'institutions': [], 'groups':[]}
        )

        in_iar_group = [
            group for group in lookup_response['groups'] if group['name'] == IAR_USERS_LOOKUP_GROUP
        ]

        if not in_iar_group:
            return Asset.objects.none()

        queryset = super(AssetViewSet, self).get_queryset()

        institutions = [institution['instid'] for institution in lookup_response['institutions']]

        return queryset.filter(Q(private=False) | Q(private=True, department__in=institutions))

    def update(self, request, *args, **kwargs):
        """We force a refresh after an update, so we can get the up to date annotation data."""
        super(AssetViewSet, self).update(request, *args, **kwargs)

        return Response(self.get_serializer(self.get_object()).data)

    def perform_destroy(self, instance):
        """perform_destroy patched to not delete the instance but instead flagged as deleted."""
        if instance.deleted_at is None:
            instance.deleted_at = now()
            instance.save()
