from django.conf.urls import url

from bulk_course_settings import (
    api,
    views)

urlpatterns = [
    url(r'^$', views.index, name='index'),

]
