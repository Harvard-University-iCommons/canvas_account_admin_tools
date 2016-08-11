from django.conf.urls import patterns, url


urlpatterns = patterns('',
    url(r'^locate_course$', 'course_selection.views.locate_course', name='locate_course'),
)
