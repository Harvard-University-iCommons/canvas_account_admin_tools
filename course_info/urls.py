from django.urls import path, re_path

from course_info import views

urlpatterns = [
    path('', views.index, name='index'),
    re_path(r'^partials/(?P<path>.+)/$', views.partials, name='partials'),
    re_path(r'^clear_sis_id/(?P<canvas_course_id>\d+)/$', views.clear_sis_id, name='clear_sis_id')
]
