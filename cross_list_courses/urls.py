from django.conf.urls import url

from cross_list_courses import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^delete_cross_listing/(?P<pk>\d+)/$', views.delete_cross_listing, name='delete_cross_listing')
]
