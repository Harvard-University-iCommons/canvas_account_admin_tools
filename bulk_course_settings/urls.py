from django.urls import path, re_path

from bulk_course_settings.views import (

    BulkSettingsListView, BulkSettingsCreateView, BulkSettingsRevertView, BulkSettingsDetailView
)

urlpatterns = [
    path('', BulkSettingsListView.as_view(), name='job_list'),
    path('create_new_job/', BulkSettingsCreateView.as_view(), name='create_new_job'),
    re_path(r'^revert_setting/(?P<school_id>[a-z]{3,7})/(?P<job_id>[0-9]{1,10})/$', BulkSettingsRevertView.as_view(), name='revert_setting'),
    re_path(r'^job_detail/(?P<job_id>[0-9]{1,10})$', BulkSettingsDetailView.as_view(), name='job_detail'),
]
