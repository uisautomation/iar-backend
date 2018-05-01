from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import routers, permissions

from assets.views import AssetViewSet, Stats


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
    path('', include(router.urls)),
    re_path(r'^(ui|docs)/$', schema_view.with_ui('swagger', cache_timeout=None),
            name='schema-openapi-ui'),
    re_path(r'^swagger(?P<format>.json|.yaml)$', schema_view.without_ui(cache_timeout=None),
            name='schema-json'),
    path('stats', Stats.as_view(), name='stats'),
]
