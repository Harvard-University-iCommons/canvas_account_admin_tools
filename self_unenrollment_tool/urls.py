from django.urls import include, path
from .views import login, launch, get_jwks, config, index, success, error

urlpatterns = [
    path('login/', login, name='login'),
    path('launch/', launch, name='launch'),
    path('jwks/', get_jwks, name='jwks'),
    path('config/', config, name='config'),
    path('index/<str:launch_id>/', index, name='index'),
    path('success/<str:launch_id>/', success, name='success'),
    path('error/', error, name='error'),
]
