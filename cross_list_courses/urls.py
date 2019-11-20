from django.urls import path, re_path

from cross_list_courses import views

urlpatterns = [
    path('', views.index, name='index'),
    re_path('add_new_pair/get_ci_data', views.get_ci_data, name='get_ci_data'),
    re_path('add_new_pair/', views.add_new_pair, name='add_new_pair'),
    re_path('create_new_pair/', views.create_new_pair, name='create_new_pair'),
    re_path(r'^delete_cross_listing/(?P<pk>\d+)/', views.delete_cross_listing, name='delete_cross_listing'),
]
