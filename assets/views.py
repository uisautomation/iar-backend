"""
Views for the assets application.

"""
from django.core.cache import cache
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from .authentication import OAuth2TokenAuthentication
from .models import Asset
from .permissions import HasScopesPermission
from .serializers import AssetSerializer


REQUIRED_SCOPES = ['assetregister']


"""
List of OAuth2 scopes required by this client.

"""


SCHEMA_DECORATOR = swagger_auto_schema(operation_security=[{'oauth2': REQUIRED_SCOPES}])
"""
Decorator to apply to DRF methods which sets the appropriate security requirements.

"""


def validate_asset_user_institution(user=None, asset_department=None):
    if user is None or asset_department is None:
        raise PermissionDenied
    institutions = map(lambda inst: inst['instid'],
                       cache.get("%s:lookup" % user.username,
                                 {'institutions': []})['institutions'])
    if asset_department not in institutions:
        raise PermissionDenied


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
    filter_fields = search_fields = ordering_fields = \
        ('id', 'name', 'department', 'purpose', 'owner', 'private', 'research',
         'personal_data', 'data_subject', 'data_category', 'recipients_category',
         'recipients_outside_eea', 'retention', 'risk_type', 'storage_location',
         'storage_format', 'paper_storage_security', 'digital_storage_security',
         'created_at', 'updated_at')

    authentication_classes = (OAuth2TokenAuthentication,)
    required_scopes = REQUIRED_SCOPES

    # TODO: Currently there are extremely permissive permissions with any valid token (even ones
    # with no associated user) being allowed to view, create and edit any asset. As we move
    # forward, we need to decide on a better permissions model based on the (client, scope, user)
    # triple.
    permission_classes = (HasScopesPermission,)

    def get_queryset(self):
        queryset = super(AssetViewSet, self).get_queryset()

        institutions = list(map(lambda inst: inst['instid'],
                                cache.get("%s:lookup" % self.request.user.username,
                                          {'institutions': []})['institutions']))
        return queryset.filter(Q(private=False) | Q(private=True, department__in=institutions))

    def create(self, request, *args, **kwargs):
        validate_asset_user_institution(request.user,
                                        request.data['department']
                                        if 'department' in request.data else None)
        return super(AssetViewSet, self).create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.get('partial', False)
        instance = self.get_object()
        validate_asset_user_institution(request.user, instance.department)
        if partial:
            if 'department' in request.data:
                validate_asset_user_institution(request.user, request.data['department'])
        else:
            validate_asset_user_institution(request.user,
                                            request.data['department']
                                            if 'department' in request.data else None)

        super(AssetViewSet, self).update(request, *args, **kwargs)
        # We force a refresh after an update, so we can get the up to date annotation data
        return Response(self.get_serializer(self.get_object()).data)

    def perform_destroy(self, instance):
        if instance.deleted_at is None:
            instance.deleted_at = now()
            instance.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        validate_asset_user_institution(request.user, instance.department)
        return super(AssetViewSet, self).destroy(request, *args, **kwargs)
