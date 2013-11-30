from django.conf.urls import patterns, url

from canvas_shopping import views

urlpatterns = patterns('',

    url(r'^index$', 'canvas_shopping.views.index', name='index'),

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
