from django.urls import path, re_path

from canvas_site_creator import views, api


urlpatterns = [
    re_path(r'^api/bulk_jobs/(?P<bulk_job_id>[\d]+)/course_jobs/', api.course_jobs, name='api_course_jobs'),
    path('api/schools/', api.schools, name='api_schools'),
    re_path(r'^api/schools/(?P<sis_account_id>[:\w]+)/course_groups/', api.course_groups, name='api_course_groups'),
    re_path(r'^api/schools/(?P<sis_account_id>[:\w]+)/departments/', api.departments, name='api_departments'),
    re_path(r'^api/schools/(?P<sis_account_id>[:\w]+)/terms/', api.terms, name='api_terms'),
    re_path(r'^api/terms/(?P<sis_term_id>[:\w]+)/accounts/(?P<sis_account_id>[:\w]+)/course_instances/', api.course_instances, name='api_course_instances'),
    re_path(r'^api/terms/(?P<sis_term_id>[:\w]+)/accounts/(?P<sis_account_id>[:\w]+)/course_instance_summary/', api.course_instance_summary, name='api_course_instance_summary'),
    path('audit/', views.audit, name='audit'),
    re_path(r'^bulk_job_detail/(?P<bulk_job_id>[\d]+)/', views.bulk_job_detail, name='bulk_job_detail'),
    path('course_selection/', views.course_selection, name='course_selection'),
    path('create_canvas_course', api.create_canvas_course_and_section, name='api_create_canvas_course'),
    path('copy_canvas_template/', api.copy_from_canvas_template, name='api_copy_from_canvas_template'),
    path('create_job/', views.create_job, name='create_job'),
    path('create_new_course/', views.create_new_course, name='create_new_course'),
    path('index/', views.index, name='index'),
    path('lti_auth_error', views.lti_auth_error, name='lti_auth_error'),
    re_path(r'^partials/(?P<path>.+)/', views.partials, name='partials'),
]
