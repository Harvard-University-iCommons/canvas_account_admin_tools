from django.conf.urls import url

from cross_list_courses import views, api

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^partials/(?P<path>.+)$', views.partials, name='partials'),
    url(r'^api/list$', api.list, name='list'),

]
