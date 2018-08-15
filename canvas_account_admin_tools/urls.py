from django.conf import settings

from django.conf.urls import include, url

from icommons_ui import views as icommons_ui_views

from canvas_account_admin_tools import views


urlpatterns = [
    url(r'^account_dashboard$', views.dashboard_account, name='dashboard_account'),
    url(r'^canvas_site_creator/', include('canvas_site_creator.urls', namespace='canvas_site_creator')),
    url(r'^course_info/', include('course_info.urls', namespace='course_info')),
    url(r'^cross_list_courses/', include('cross_list_courses.urls', namespace='cross_list_courses')),
    url(r'^icommons_rest_api/(?P<path>.*)$', views.icommons_rest_api_proxy, name='icommons_rest_api_proxy'),
    url(r'^lti_auth_error$', icommons_ui_views.not_authorized, name='lti_auth_error'),
    url(r'^lti_launch$', views.lti_launch, name='lti_launch'),
    url(r'^not_authorized$', icommons_ui_views.not_authorized, name='not_authorized'),
    url(r'^people_tool/', include('people_tool.urls', namespace='people_tool')),
    url(r'^publish_courses/', include('publish_courses.urls', namespace='publish_courses')),
    url(r'^bulk_course_settings/', include('bulk_course_settings.urls', namespace='bulk_course_settings')),

    url(r'^tool_config$', views.tool_config, name='tool_config'),
]

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass  # This is OK for a deployed instance running in DEBUG mode
