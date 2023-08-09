from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('download/<path:s3_key>/<str:filename>',
         views.download, name='download'),
    path('errors/<str:pk>/<str:sk>/', views.errors, name='errors'),
    path('help', views.help, name='help'),
]
