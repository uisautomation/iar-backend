"""
Views for the assets application.

"""
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.pagination import CursorPagination

from .authentication import OAuth2TokenAuthentication
from .models import Asset
from .permissions import HasScopesPermission
from .serializers import AssetSerializer

REQUIRED_SCOPES = ['lookup:anonymous', 'assetregister']
"""
List of OAuth2 scopes required by this client.

"""


class AssetCursorPagination(CursorPagination):
    """Custom Ordering for Asset"""
    ordering = '-created_at'


SCHEMA_DECORATOR = swagger_auto_schema(operation_security=[{'oauth2': REQUIRED_SCOPES}])
"""
Decorator to apply to DRF methods which sets the appropriate security requirements.

"""


@method_decorator(name='create', decorator=SCHEMA_DECORATOR)
@method_decorator(name='retrieve', decorator=SCHEMA_DECORATOR)
@method_decorator(name='update', decorator=SCHEMA_DECORATOR)
@method_decorator(name='partial_update', decorator=SCHEMA_DECORATOR)
@method_decorator(name='destroy', decorator=SCHEMA_DECORATOR)
@method_decorator(name='list', decorator=SCHEMA_DECORATOR)
class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows assets to be viewed or edited.

    """
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    pagination_class = AssetCursorPagination

    authentication_classes = (OAuth2TokenAuthentication,)
    required_scopes = REQUIRED_SCOPES

    # TODO: Currently there are extremely permissive permissions with any valid token (even ones
    # with no associated user) being allowed to view, create and edit any asset. As we move
    # forward, we need to decide on a better permissions model based on the (client, scope, user)
    # triple.
    permission_classes = (HasScopesPermission,)
