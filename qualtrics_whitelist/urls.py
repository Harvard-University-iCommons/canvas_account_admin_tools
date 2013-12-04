from django.conf.urls import patterns, include, url

from qualtrics_whitelist.views import QualtricsAccessListView, QualtricsAccessSearchView, QualtricsAccessEditView, QualtricsAccessDeleteView, QualtricsAccessAddView, QualtricsAccessResultsListView

urlpatterns = patterns('',

    url(r'^$', QualtricsAccessListView.as_view(), name='qualtricsaccesslist'),
    url(r'^qualtrics_access_search/$', QualtricsAccessSearchView.as_view(), name='access_searchfor'),
    url(r'^qualtrics_access_add/$', QualtricsAccessAddView.as_view(), name='access_addview'),
    url(r'^qualtrics_access_delete/$', QualtricsAccessDeleteView.as_view(), name='access_confirmdelete'),
    url(r'^qualtrics_access_edit/$', QualtricsAccessEditView.as_view(), name='access_editview'),
    url(r'^qualtrics_access_results_list/$', QualtricsAccessResultsListView.as_view(), name='access_resultsview'),

)