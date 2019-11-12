from django.urls import path, re_path

from canvas_site_deletion import views

urlpatterns = [
    path('', views.index, name='index'),
    path('lookup', views.lookup, name='lookup'),
    re_path(r'^delete/(?P<pk>\d+)/', views.delete, name='delete'),
]
