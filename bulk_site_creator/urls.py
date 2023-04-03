from django.urls import path

from bulk_site_creator import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create_bulk_job', views.create_bulk_job, name='create_bulk_job'),
]
