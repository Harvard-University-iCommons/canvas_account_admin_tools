from django.conf.urls import url

from publish_courses import (
    api,
    views)

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^api/jobs$', api.BulkPublishListCreate.as_view(), name='api_jobs'),
    url(r'^api/show_summary$', api.SummaryList.as_view(), name='api_show_summary'),
    url(r'^partials/(?P<path>.+)$', views.partials, name='partials'),
]
