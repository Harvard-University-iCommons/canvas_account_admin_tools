from django.conf.urls import url

from cross_list_courses_v2 import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
]
