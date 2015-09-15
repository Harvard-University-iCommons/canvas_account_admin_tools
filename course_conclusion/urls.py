from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static

from . import api, views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^api/courses$', api.courses, name='api_courses'),
    url(r'^api/courses/(?P<course_instance_id>\d+)$', api.course,
        name='api_course'),
    url(r'^api/concluded_courses_by_school$', api.concluded_courses_by_school,
        name='api_concluded_courses_by_school'),
    url(r'^api/concluded_courses_by_school_term$', api.concluded_courses_by_school_term,
        name='concluded_courses_by_school_term'),
    url(r'^api/schools$', api.schools, name='api_schools'),
    url(r'^api/terms$', api.terms, name='api_terms'),
]
