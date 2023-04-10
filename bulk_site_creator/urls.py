from django.urls import path

from bulk_site_creator import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create_bulk_job', views.create_bulk_job, name='create_bulk_job'),
    path('new_job', views.new_job, name='new_job'),
    path(r'^job_detail/(?P<job_id>[0-9]{1,10})/', views.job_detail, name='job_detail'),
]
