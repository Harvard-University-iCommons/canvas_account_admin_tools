from django.urls import path

from self_enrollment_tool import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add_new/', views.add_new, name='add_new'),
    path('lookup/', views.lookup, name='lookup'),
    path('enable/<int:course_instance_id>/', views.enable,  name='enable'),
    path('disable/<uuid:uuid>/', views.disable, name='disable'),
]
