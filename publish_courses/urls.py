from django.conf.urls import url

from publish_courses import (
    api,
    views)

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^api/jobs$', api.BulkPublishListCreate.as_view(), name='api_jobs'),
    url(r'^api/course_list$', api.CourseDetailList.as_view(), name='api_course_list'),
    url(r'^partials/(?P<path>.+)$', views.partials, name='partials'),
]
