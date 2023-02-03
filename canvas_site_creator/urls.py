from django.urls import path, re_path

from canvas_site_creator import views, api


urlpatterns = [
    re_path(r'^create_new_course/', views.create_new_course, name='create_new_course'),
    path('lti_auth_error', views.lti_auth_error, name='lti_auth_error'),
]
