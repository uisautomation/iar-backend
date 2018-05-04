"""
Views for the assets application.
"""
from collections import namedtuple
from automationlookup.lookup import get_person_for_user
from automationcommon.models import set_local_user, clear_local_user
from automationoauthdrf.authentication import OAuth2TokenAuthentication
from django.conf import settings
from django.db.models import Q, Count
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django_filters.rest_framework import (
    DjangoFilterBackend, FilterSet, CharFilter, BooleanFilter, ChoiceFilter
)
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, generics
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response

from .models import Asset
from .permissions import (
    OrPermission, AndPermission,
    HasScopesPermission, UserInInstitutionPermission, UserInIARGroupPermission
)
from .serializers import AssetSerializer, AssetStatsSerializer


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
    # It seem's probable that we would like to filter on the following MultiSelectField fields.
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
        """
        get_queryset is patched to only return those assets that are not private or that are
        private but the user doing the request belongs to department that owns the asset.

        Also, if the user is not in :py:attr:`~assets.defaultsettings.IAR_USERS_LOOKUP_GROUP`,
        they can't see assets.
        """

        lookup_response = get_person_for_user(self.request.user)

        in_iar_group = [
            group for group in lookup_response['groups']
            if group['name'] == settings.IAR_USERS_LOOKUP_GROUP
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


AssetCounts = namedtuple('AssetCounts', 'total completed with_personal_data')


class AssetStats:
    """Given a queryset of matching non-annotated asset records, calculate some statistics for all
    assets and assets grouped by department.
    We need the non-annotated queryset to work around a bug in Django. See
    https://code.djangoproject.com/ticket/28762 and
    https://github.com/uisautomation/iar-backend/issues/55.

    :param queryset: Non-annotated queryset of :py:class:`assets.models.Asset` objects

    :ivar AssetCounts all: Counts for all assets
    :ivar dict by_institution: An :py:class:`AssetCounts` instance for each institution keyed by
        Lookup instid.

    """

    def __init__(self, queryset):
        # Annotate the input queryset with is_complete.
        annotated_queryset = Asset.objects.annotate_is_complete(queryset)

        # Compute asset entry counts for all assets.
        self.all = AssetCounts(
            total=queryset.count(),
            # This works around bug that throws an exception
            completed=queryset.filter(
                id__in=annotated_queryset.filter(is_complete=True).values('id')).count(),
            with_personal_data=queryset.filter(personal_data=True).count()
        )

        # Compute individual counts grouped by department for each class of entry.
        n_assets_by_dept = {
            d['department']: d['count'] for d in
            queryset.values('department').annotate(count=Count('id')).order_by('department')
        }
        n_assets_completed_by_dept = {
            d['department']: d['count'] for d in
            annotated_queryset.filter(is_complete=True).values('department')
            .annotate(count=Count('id')).order_by('department')
        }
        n_assets_with_personal_data_by_dept = {
            d['department']: d['count'] for d in
            queryset.filter(personal_data=True)
            .values('department').annotate(count=Count('id')).order_by('department')
        }

        # Create a list of all departments in the database
        all_depts = [
            row['department'] for row in
            queryset.distinct('department').values('department').order_by('department')
        ]

        # Collect separate counts together grouped by institution. If there is no count for a
        # particular institution, report "0".
        self.by_institution = {
            dept: AssetCounts(
                total=n_assets_by_dept.get(dept, 0),
                completed=n_assets_completed_by_dept.get(dept, 0),
                with_personal_data=n_assets_with_personal_data_by_dept.get(dept, 0),
            )
            for dept in all_depts
        }


class Stats(generics.RetrieveAPIView):
    """
    Returns Assets stats: total number of assets, total number of assets completed,
    total number of assets with personal data, and assets per department (total, completed,
    with personal data)
    """
    serializer_class = AssetStatsSerializer

    def get_object(self):
        # These statistics should only be for non-deleted assets.
        return AssetStats(Asset.objects.get_base_queryset().filter(deleted_at__isnull=True))
