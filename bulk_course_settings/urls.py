from django.conf.urls import include, url

from bulk_course_settings.views import (
    BulkSettingsListView,
    BulkSettingsCreateView,
)

urlpatterns = [
    url(r'^$', BulkSettingsListView.as_view(), name='bulk_settings_list'),
    url(r'^create_new_setting$', BulkSettingsCreateView.as_view(), name='create_new_setting'),
]
