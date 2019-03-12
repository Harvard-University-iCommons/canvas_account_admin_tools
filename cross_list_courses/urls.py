from django.conf.urls import url

from cross_list_courses import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^add_new_pair', views.add_new_pair, name='add_new_pair'),
    url(r'^create_new_pair', views.create_new_pair, name='create_new_pair'),

]
