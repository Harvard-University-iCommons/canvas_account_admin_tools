from django.conf.urls import url

from publish_courses import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^partials/(?P<path>.+)$', views.partials, name='partials'),
]
