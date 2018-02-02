from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import routers, permissions
from assets.views import AssetViewSet, AssetAdvanceList

# Django Rest Framework Routing
router = routers.DefaultRouter()
router.register(r'assets', AssetViewSet)

schema_view = get_schema_view(
   openapi.Info(
      title="Information Asset Register API",
      default_version='v1',
      description="University of Cambridge Information Asset Register API",
      # terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="automation@uis.cam.ac.uk"),
      # license=openapi.License(name="BSD License"),
   ),
   validators=['flex', 'ssv'],
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('assets/advanced-list/', AssetAdvanceList.as_view(), name="assets-advanced-list"),
    path('', include(router.urls)),
    path('openapi/', schema_view.with_ui('swagger', cache_timeout=None), name='schema-openapi-ui'),
    re_path(r'^swagger(?P<format>.json|.yaml)$', schema_view.without_ui(cache_timeout=None),
            name='schema-json'),
]
