from django.urls import path, re_path

from masquerade_tool import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add_role/', views.add_role, name='add_role'),
    # re_path(r'^delete/(?P<pk>\d+)/', views.delete, name='delete'),
]