from django.conf.urls import patterns, url

from .views import JobListView

urlpatterns = patterns('',
    url(r'^$', JobListView.as_view(), name='job_list'),
    url(r'^archive/$', JobListView.as_view(archive=True), name='job_list_archive'),
)
