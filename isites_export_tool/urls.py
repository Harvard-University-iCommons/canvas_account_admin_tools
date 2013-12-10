from django.conf.urls import patterns, url

from .views import JobListOrCreate

urlpatterns = patterns('',
    url(r'^$', JobListOrCreate.as_view(), name='job_list'),
    url(r'^archive/$', JobListOrCreate.as_view(archive=True), name='job_list_archive'),
)
