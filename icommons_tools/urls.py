from django.conf.urls import include, url

urlpatterns = [
    url(r'^icommons_ui/', include('icommons_ui.urls')),
    url(r'^canvas_whitelist/', include('canvas_whitelist.urls', namespace="cwl")),
    url(r'^course_conclusion/', include('course_conclusion.urls', namespace='cc')),
    url(r'^isites_export/', include('isites_export_tool.urls', namespace="et")),
    url(r'^not_authorized/', 'icommons_ui.views.not_authorized', name="not_authorized"),
    url(r'^pin/', include('icommons_common.auth.urls', namespace="pin")),
    url(r'^qualtrics_taker_auth/', include('qualtrics_taker_auth.urls', namespace="qta")),
    url(r'^qualtrics_whitelist/', include('qualtrics_whitelist.urls', namespace="qwl")),
    url(r'^shopping/', include('canvas_shopping.urls', namespace="sh")),
    url(r'^term_tool/', include('term_tool.urls', namespace="tt")),
]
