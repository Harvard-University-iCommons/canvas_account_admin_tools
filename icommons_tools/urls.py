from django.conf.urls import patterns, include, url

urlpatterns = [
    url(r'^icommons_ui/', include('icommons_ui.urls')),
    url(r'^tools/canvas_whitelist/', include('canvas_whitelist.urls', namespace="cwl")),
    url(r'^tools/course_conclusion/', include('course_conclusion.urls', namespace='cc')),
    url(r'^tools/isites_export/', include('isites_export_tool.urls', namespace="et")),
    url(r'^tools/not_authorized/', 'icommons_ui.views.not_authorized', name="not_authorized"),
    url(r'^tools/pin/', include('icommons_common.auth.urls', namespace="pin")),
    url(r'^tools/qualtrics_taker_auth/', include('qualtrics_taker_auth.urls', namespace="qta")),
    url(r'^tools/qualtrics_whitelist/', include('qualtrics_whitelist.urls', namespace="qwl")),
    url(r'^tools/shopping/', include('canvas_shopping.urls', namespace="sh")),
    url(r'^tools/term_tool/', include('term_tool.urls', namespace="tt")),
]
