from django.conf.urls import url

from bulk_course_settings.views import (

    BulkSettingsListView, BulkSettingsCreateView, BulkSettingsRevertView, BulkSettingsDetailView
)

urlpatterns = [
    url(r'^$', BulkSettingsListView.as_view(), name='job_list'),
    url(r'^create_new_job/$', BulkSettingsCreateView.as_view(), name='create_new_job'),
    url(r'^revert_setting/(?P<school_id>[a-z]{3,7})/(?P<job_id>[0-9]{1,10})/$', BulkSettingsRevertView.as_view(), name='revert_setting'),
    url(r'^job_detail/(?P<job_id>[0-9]{1,10})$', BulkSettingsDetailView.as_view(), name='job_detail'),
]
