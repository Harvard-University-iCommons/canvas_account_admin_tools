from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static

from . import api, views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^api/courses', api.courses, name='api_courses'),
    url(r'^api/schools', api.schools, name='api_schools'),
    url(r'^api/terms', api.terms, name='api_terms'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
