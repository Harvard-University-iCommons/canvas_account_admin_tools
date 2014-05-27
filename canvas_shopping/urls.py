from django.conf.urls import patterns, url

from canvas_shopping import views

urlpatterns = patterns('',

    url(r'^add_shopper_ui$', 'canvas_shopping.views.add_shopper_ui', name='add_shopper_ui'),

    url(r'^remove_shopper_ui$', 'canvas_shopping.views.remove_shopper_ui', name='remove_shopper_ui'),

    url(r'^course/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.course', name='course'),

    url(r'^course_selfreg/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.course_selfreg', name='course'),

    url(r'^$', views.SchoolListView.as_view(), name='schoollist'),

    url(r'^(?P<school_id>\w+)$', views.CourseListView.as_view(), name='courselist'),


)




'''
    url(
        regex=r"^api/(?<school_id>\w+)/(?<academic_year>\d{4})/(?<term_code>\d+)/(?<course_id>\w+)/(?<user_id>\w+)$",
        view='views.remove_shopper',
        name='remove_shopper',
    ),

    url(
        regex=r"^api/(?<school_id>\w+)/(?<academic_year>\d{4})/(?<term_code>\d+)/(?<course_id>\w+)$",
        view='views.add_shopper',
        name='add_shopper',
    ),
'''
