from django.urls import path, re_path

from self_enrollment_tool import views

urlpatterns = [
    path('', views.index, name='index'),
    path('lookup/', views.lookup, name='lookup'),
    path('enable/', views.lookup, name='enable'),
    path('enroll/', views.lookup, name='enroll'),

]
