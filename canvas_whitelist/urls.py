from django.conf.urls import patterns, include, url

from canvas_whitelist import views
from canvas_whitelist.views import CanvasAccessListView, CanvasAccessSearchView, CanvasAccessEditView, CanvasAccessConfirmDeleteView, CanvasAccessResultsListView

urlpatterns = patterns('',

    url(r'^$', CanvasAccessListView.as_view(), name='canvasaccesslist'),

    url(r'^canvas_access_search/$', CanvasAccessSearchView.as_view(), name='access_searchfor'),
    url(r'^canvas_access_update/$', views.access_update_person, name='access_update'),
    url(r'^canvas_access_confirmdelete/(?P<pk>\d+)/$', CanvasAccessConfirmDeleteView.as_view(), name='access_confirmdelete'),
    url(r'^canvas_access_delete/$', views.delete, name='delete'),
    url(r'^canvas_access_edit/(?P<pk>\d+)/$', CanvasAccessEditView.as_view(), name='access_editview'),
    url(r'^canvas_access_results_list/$', CanvasAccessResultsListView.as_view(), name='access_resultsview'),
    

)