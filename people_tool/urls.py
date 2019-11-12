from django.urls import path, re_path

from people_tool import views

urlpatterns = [
    path('', views.index, name='index'),
    re_path(r'^partials/(?P<path>.+)', views.partials, name='partials'),
]
