from django.conf.urls import patterns, url

from .views import JobsIndexView

urlpatterns = patterns('',
    
    url(r'^', JobsIndexView.as_view(), name='jobs_index'),
)
