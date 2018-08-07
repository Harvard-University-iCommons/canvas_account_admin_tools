from django.conf.urls import url

from bulk_course_settings.views import (

    BulkSettingsListView, BulkSettingsCreateView, BulkSettingsRevertView, BulkSettingsAuditView
)

urlpatterns = [
    url(r'^$', BulkSettingsListView.as_view(), name='bulk_settings_list'),
    url(r'^create_new_setting/$', BulkSettingsCreateView.as_view(), name='create_new_setting'),
    url(r'^revert_setting/(?P<school_id>[a-z]{3,7})/(?P<job_id>[0-9]{1,10})/$', BulkSettingsRevertView.as_view(), name='revert_setting'),
    url(r'^bulk_settings_job_audit/(?P<job_id>[0-9]{1,10})$', BulkSettingsAuditView.as_view(), name='bulk_settings_job_audit'),
]
