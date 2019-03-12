from django.conf.urls import url

from course_info import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^partials/(?P<path>.+)$', views.partials, name='partials'),
    url(r'^clear_sis_id/(?P<canvas_course_id>\d+)/$', views.clear_sis_id, name='clear_sis_id')
]
