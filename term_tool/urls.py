from django.conf.urls import patterns, include, url

from term_tool.views import SchoolListView, TermListView, TermEditView, TermCreateView

urlpatterns = patterns('',

	url(r'^$', SchoolListView.as_view(), name='schoollist'),
	
	url(r'^(?P<school_id>\w+)/term_list/$', TermListView.as_view(), name='termlist'),

	url(r'^term/(?P<pk>\d+)/edit$', TermEditView.as_view(), name='termedit'),

	url(r'^term/new/(?P<school_id>\w+)$', TermCreateView.as_view(), name='termcreate'),

	url(r'^logout$', 'term_tool.views.logout_view', name='logout'),

	url(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'term_tool/login.html'}, name='login'),

	url(r'^logged_out$', 'term_tool.views.logged_out_view', name='logged_out'),

)

