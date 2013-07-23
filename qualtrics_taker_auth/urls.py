from django.conf.urls import patterns, url

from qualtrics_taker_auth import views

urlpatterns = patterns('',

    url(r'^$', views.index, name='index'),
    

)

