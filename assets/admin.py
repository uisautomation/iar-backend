from django.contrib import admin
from assets.models import Asset


class AssetAdmin(admin.ModelAdmin):
    exclude = ('created_at', 'updated_at')
    list_display = ('name', 'department', 'owner')

    def get_queryset(self, request):
        # We use the "base" queryset here because the admin does not like the is_complete
        # annotation.
        return Asset.objects.get_base_queryset()


admin.site.register(Asset, AssetAdmin)
