from django.conf.urls import patterns, url

from canvas_shopping import views

urlpatterns = patterns('',

    url(r'^add_shopper_ui$', 'canvas_shopping.views.add_shopper_ui', name='add_shopper_ui'),

    url(r'^remove_shopper_ui$', 'canvas_shopping.views.remove_shopper_ui', name='remove_shopper_ui'),

    url(r'^course/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.view_course', name='course'),

    url(r'^view_course/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.view_course', name='view_course'),

    url(r'^shop_course/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.shop_course', name='shop_course'),

    url(r'^remove_shopper_role/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.remove_shopper_role', name='remove_shopper_role'),

    url(r'^remove_viewer_role/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.remove_viewer_role', name='remove_viewer_role'),

    url(r'^remove_role/(?P<role>\w+)/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.remove_role', name='remove_role'),

    url(r'^course_selfreg/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.course_selfreg', name='course_selfreg'),

    url(r'my_list$', 'canvas_shopping.views.my_list', name='my_list'),

)

