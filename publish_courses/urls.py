from django.urls import path, re_path

from publish_courses import (
    api,
    views)

urlpatterns = [
    path('', views.index, name='index'),
    re_path(r'^api/jobs/', api.BulkPublishListCreate.as_view(), name='api_jobs'),
    re_path(r'^api/course_list/', api.CourseDetailList.as_view(), name='api_course_list'),
    re_path(r'^partials/(?P<path>.+)/', views.partials, name='partials'),
]
