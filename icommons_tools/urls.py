from django.conf.urls import patterns, include, url

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

    url(r'^tools/qualtrics_whitelist/', include('qualtrics_whitelist.urls', namespace="qwl")),

    url(r'^tools/canvas_whitelist/', include('canvas_whitelist.urls', namespace="cwl")),

    url(r'^icommons_ui/', include('icommons_ui.urls')),

    url(r'^tools/not_authorized/', 'icommons_ui.views.not_authorized', name="not_authorized"),

)
