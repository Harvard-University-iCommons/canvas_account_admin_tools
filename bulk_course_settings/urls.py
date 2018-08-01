from django.conf.urls import include, url

from bulk_course_settings.views import (
    BulkSettingsListView, BulkSettingsCreateView, BulkSettingsRevertView, add_bulk_job
)

urlpatterns = [
    url(r'^$', BulkSettingsListView.as_view(), name='bulk_settings_list'),
    url(r'^create_new_setting/$', BulkSettingsCreateView.as_view(), name='create_new_setting'),
    url(r'^revert_setting/$', BulkSettingsRevertView.as_view(), name='revert_setting'),

    url(r'^add_bulk_job/$', add_bulk_job, name='add_bulk_job'),

]
