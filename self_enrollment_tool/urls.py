from django.urls import path

from self_enrollment_tool import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add_new/', views.add_new, name='add_new'),
    path('lookup/', views.lookup, name='lookup'),
    path('enable/<int:course_instance_id>/', views.enable,  name='enable'),
    path('enroll/<int:course_instance_id>/', views.enroll, name='enroll'),
    path('disable/<int:pk>/',
         views.disable, name='disable'),
    path('delete_user_from_course/<int:course_instance_id>/<int:user_id>',
         views.delete_user_from_course, name='delete_user_from_course')
]
