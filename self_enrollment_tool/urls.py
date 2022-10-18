from django.urls import path, re_path

from self_enrollment_tool import views

urlpatterns = [
    path('', views.index, name='index'),
    path('lookup/', views.lookup, name='lookup'),
    re_path(r'^enable/(?P<course_instance_id>\d+)/$', views.enable, name='enable'),
    re_path(r'^enroll/(?P<course_instance_id>\d+)/$', views.enroll, name='enroll'),
    re_path(r'^remove_self_enroll/(?P<pk>\d+)/$', views.remove_self_enroll, name='remove_self_enroll'),
]
