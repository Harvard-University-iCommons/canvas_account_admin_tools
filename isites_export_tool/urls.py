from django.conf.urls import patterns, url

from .views import JobListView, MonitorResponseView, download_export_file

urlpatterns = patterns(
    '',
    url(r'^$', JobListView.as_view(), name='job_list'),
    url(r'^archive/$', JobListView.as_view(archive=True), name='job_list_archive'),
    url(r'^monitor/$', MonitorResponseView.as_view()),
    url(r'^download_export/$', 'isites_export_tool.views.download_export_file', name='download_export_file'),
)
