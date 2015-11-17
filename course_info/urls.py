from django.conf.urls import url

from course_info import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^partials/(?P<path>.+)$', views.partials, name='partials'),
]
