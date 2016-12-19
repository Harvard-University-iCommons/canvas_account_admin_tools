from django.conf.urls import url

from publish_courses import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^api/publish$', views.api_publish, name='api_publish'),
    url(r'^partials/(?P<path>.+)$', views.partials, name='partials'),
]
