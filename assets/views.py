from rest_framework import viewsets
from assets.models import Asset
from assets.serializers import AssetSerializer
from rest_framework.pagination import CursorPagination


class AssetCursorPagination(CursorPagination):
    """Custom Ordering for Asset"""
    ordering = '-created_at'


class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows assets to be viewed or edited.
    """
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    pagination_class = AssetCursorPagination
