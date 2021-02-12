from django.urls import path

from masquerade_tool import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add_role/', views.add_role, name='add_role'),
]
