from django.conf.urls import patterns, url

urlpatterns = patterns('',

    url(r'^remove_shopper_ui$', 'canvas_shopping.views.remove_shopper_ui', name='remove_shopper_ui'),

    url(r'^shop_course/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.shop_course', name='shop_course'),

    url(r'^remove_shopper_role/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.remove_shopper_role', name='remove_shopper_role'),

    url(r'^course_selfreg/(?P<canvas_course_id>\d+)$', 'canvas_shopping.views.course_selfreg', name='course_selfreg'),

    url(r'my_list$', 'canvas_shopping.views.my_list', name='my_list'),

)

