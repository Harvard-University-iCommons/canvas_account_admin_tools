from django.urls import path

from self_enrollment_tool import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add_new/', views.add_new, name='add_new'),
    path('lookup/', views.lookup, name='lookup'),
    path('enable/<int:course_instance_id>/', views.enable,  name='enable'),
    path('enroll/<int:course_instance_id>/', views.enroll, name='enroll'),
    path('remove_self_enroll/<int:pk>/', views.remove_self_enroll, name='remove_self_enroll'),
]
