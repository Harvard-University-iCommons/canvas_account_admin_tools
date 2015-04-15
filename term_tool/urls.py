from django.conf.urls import patterns, include, url

from term_tool.views import (SchoolListView, TermListView, TermEditView, TermCreateView, ExcludeCoursesFromViewing)
urlpatterns = patterns('',

    url(r'^$', SchoolListView.as_view(), name='schoollist'),
    
    url(r'^(?P<school_id>\w+)/term_list/$', TermListView.as_view(), name='termlist'),

    url(r'^term/(?P<pk>\d+)/edit$', TermEditView.as_view(), name='termedit'),

    url(r'^term/new/(?P<school_id>\w+)$', TermCreateView.as_view(), name='termcreate'),

    url(r'^term/(?P<term_id>\d+)/(?P<school_id>\w+)/exlude_courses$', ExcludeCoursesFromViewing.as_view(), name='excludecourses')

)

