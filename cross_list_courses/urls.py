from django.conf.urls import url

from cross_list_courses import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
]
