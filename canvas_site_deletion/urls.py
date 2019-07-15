from django.conf.urls import url

from canvas_site_deletion import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^lookup$', views.lookup, name='lookup'),
    url(r'^delete/(?P<pk>\d+)/$', views.delete, name='delete'),
]
