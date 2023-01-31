from django.urls import path

from bulk_site_creator import views

urlpatterns = [
    path('', views.index, name='index'),
]
