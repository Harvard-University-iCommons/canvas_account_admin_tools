from django.conf.urls import patterns, include, url

from qualtrics_whitelist.views import QualtricsAccessListView

urlpatterns = patterns('',

    url(r'^$', QualtricsAccessListView.as_view(), name='qualtricsacceslist'),
    
    

)