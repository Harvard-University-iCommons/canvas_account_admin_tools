import watchman.views
from django.conf import settings
from django.urls import include, path, re_path
from icommons_ui import views as icommons_ui_views

from canvas_account_admin_tools import views

urlpatterns = [
    path('account_dashboard', views.dashboard_account, name='dashboard_account'),
    path('bulk_enrollment_tool/', include(('bulk_enrollment_tool.urls', 'bulk_enrollment_tool'), namespace='bulk_enrollment_tool')),
    path('canvas_site_creator/', include(('canvas_site_creator.urls', 'canvas_site_creator'), namespace='canvas_site_creator')),
    path('course_info/', include(('course_info.urls', 'course_info'), namespace='course_info')),
    path('course_info_v2/', include(('course_info_v2.urls', 'course_info_v2'), namespace='course_info_v2')),
    path('cross_list_courses/', include(('cross_list_courses.urls', 'cross_list_courses'), namespace='cross_list_courses')),
    re_path(r'^icommons_rest_api/(?P<path>.*)/', views.icommons_rest_api_proxy, name='icommons_rest_api_proxy'),
    path('lti_auth_error', icommons_ui_views.not_authorized, name='lti_auth_error'),
    path('lti_launch', views.lti_launch, name='lti_launch'),
    path('not_authorized', icommons_ui_views.not_authorized, name='not_authorized'),
    path('people_tool/', include(('people_tool.urls', 'people_tool'), namespace='people_tool')),
    path('publish_courses/', include(('publish_courses.urls', 'publish_courses'), namespace='publish_courses')),
    path('bulk_course_settings/', include(('bulk_course_settings.urls', 'bulk_course_settings'), namespace='bulk_course_settings')),
    path('canvas_site_deletion/', include(('canvas_site_deletion.urls', 'canvas_site_deletion'), namespace='canvas_site_deletion')),
    path('masquerade_tool/', include(('masquerade_tool.urls', 'masquerade_tool'), namespace='masquerade_tool')),
    path('self_enrollment_tool/', include(('self_enrollment_tool.urls', 'self_enrollment_tool'), namespace='self_enrollment_tool')),
    path('self_unenrollment_tool/', include(('self_unenrollment_tool.urls', 'self_unenrollment_tool'), namespace='self_unenrollment_tool')),
    path('bulk_site_creator/', include(('bulk_site_creator.urls', 'bulk_site_creator'), namespace='bulk_site_creator')),
    path('tool_config/', views.tool_config, name='tool_config'),
    path('w/', include('watchman.urls')),
    re_path(r'^status/?$', watchman.views.bare_status),
]

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [
            re_path(r'^__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass  # This is OK for a deployed instance running in DEBUG mode
