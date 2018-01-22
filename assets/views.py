from rest_framework import viewsets
from assets.models import Asset
from assets.serializers import AssetSerializer


class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows assets to be viewed or edited.
    """
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
