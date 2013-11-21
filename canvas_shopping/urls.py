from django.conf.urls import patterns, include, url

from canvas_shopping.views import *

urlpatterns = patterns('',

    url(r'^$', 'canvas_shopping.views.index'),

    url(r'^shop$', 'canvas_shopping.views.shop'),

)

