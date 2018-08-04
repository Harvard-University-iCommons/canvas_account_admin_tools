from django.conf.urls import url

from bulk_course_settings.views import (
    BulkSettingsListView, BulkSettingsCreateView, BulkSettingsRevertView
)

urlpatterns = [
    url(r'^$', BulkSettingsListView.as_view(), name='bulk_settings_list'),
    url(r'^create_new_setting/$', BulkSettingsCreateView.as_view(), name='create_new_setting'),
    url(r'^revert_setting/(?P<school_id>[a-z]{3,7})/(?P<job_id>[0-9]{1,4})/$', BulkSettingsRevertView.as_view(), name='revert_setting'),
]
