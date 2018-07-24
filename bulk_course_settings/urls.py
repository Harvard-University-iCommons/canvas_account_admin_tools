from django.conf.urls import url

from bulk_course_settings.views import (
    BulkSettingsListView, BulkSettingsCreateView, add_bulk_job
)


urlpatterns = [
    url(r'^$', BulkSettingsListView.as_view(), name="bulk_settings_list"),
    url(r'^create_new_settings/$', BulkSettingsCreateView.as_view(), name='create_new'),
    url(r'^add_bulk_job/$', add_bulk_job, name='add_bulk_job'),

]
