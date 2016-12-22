from django.conf.urls import url

from publish_courses import (
    api,
    views)

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^api/publish$', api.publish, name='api_publish'),
    url(r'^partials/(?P<path>.+)$', views.partials, name='partials'),
]
