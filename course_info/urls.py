from django.conf.urls import url

from course_info import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^enrollments/(?P<course_instance_id>\d+)/$', views.enrollments,
        name='enrollments'),
]
