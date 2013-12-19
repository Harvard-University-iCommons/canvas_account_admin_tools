from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'icommons_tools.views.home', name='home'),
    # url(r'^icommons_tools/', include('icommons_tools.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/', include(admin.site.urls)),

    url(r'^tools/term_tool/', include('term_tool.urls', namespace="tt")),

    url(r'^tools/qualtrics_taker_auth/', include('qualtrics_taker_auth.urls', namespace="qta")),

    url(r'^tools/isites_export/', include('isites_export_tool.urls', namespace="et")),

    url(r'^tools/shopping/', include('canvas_shopping.urls', namespace="sh")),

    url(r'^tools/pin/', include('icommons_common.auth.urls', namespace="pin")),

    url(r'^tools/sample/', TemplateView.as_view(template_name="icommons_tools/sample.html"), name="sample"),
    url(r'^tools/sample-dn/', TemplateView.as_view(template_name="icommons_tools/sample-defaultnav.html"), name="sample-dn"),
    url(r'^tools/sample-jt/', TemplateView.as_view(template_name="icommons_tools/sample-jumbotron.html"), name="sample-jt"),

)
