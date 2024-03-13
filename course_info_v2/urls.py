from posixpath import relpath
from django.urls import path

from course_info_v2 import views

urlpatterns = [
    path("", views.index, name="index"),
    path("details/", views.details, name="details")
]
