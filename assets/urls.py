from django.urls import path, include, re_path
from rest_framework import routers, permissions
from assets.views import AssetViewSet

# Django Rest Framework Routing
router = routers.DefaultRouter()
router.register(r'assets', AssetViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
