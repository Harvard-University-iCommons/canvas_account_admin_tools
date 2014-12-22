from django.http import QueryDict
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from icommons_common.canvas_utils import *
from django.conf import settings
from functools import wraps
import logging
import re

group_pattern = re.compile('LdapGroup:[a-z]+\.student')
CAS_LOGOUT_URL = settings.CAS_LOGOUT_URL

logger = logging.getLogger(__name__)


def check_user_id_integrity(login_id_required=True, missing_login_id_redirect_url=None):
    """
    Decorator to check if tool user is the same as the Canvas user
    Usage: decorate the View with check_user_id_integrity() or add arguments as needed
           * Note the parentheses are required even when no arguments are passed,
             as this is actually a decorator factory, not a bare decorator.
    """
    def decorator(view_func):
        @wraps(view_func)
        @require_http_methods(['GET'])
        def wrapper(request, *args, **kwargs):
            # Check for 'canvas_login_id', which will be passed in by shop.js
            # on the Canvas instance. If it's not present the code will skip this
            # block and continue on. If it's present, verify that it matches the
            # user_id in the tool. If there is a mismatch, send user to pin logout
            # (this is the current security patch, maybe modified with a better solution.)

            # check for canvas_login_id parameter; this decorator could be used
            # for POST, GET, PUT, etc so use a generic method of accessing the parameter
            params = QueryDict(request.body)

            # canvas_login_id is the 'login_id' attribute from the Canvas
            # user profile. It is essentially the Canvas sis_user_id (e.g. HUID)
            canvas_login_id = params.get('canvas_login_id')
            if canvas_login_id:
                user_id = request.user.username
                logger.debug('user id integrity check: user in tool=%s, '
                             'canvas_login_id from request == %s' % (user_id, canvas_login_id))

                if str(user_id) != str(canvas_login_id):
                    logger.error('user integrity mismatch: user in tool=%s, canvas_login_id from request=%s. '
                                 'Logging out the user from CAS' % (user_id, canvas_login_id))
                    return redirect(CAS_LOGOUT_URL)
            elif login_id_required:
                # canvas_login_id is required to access the calling function
                # but was not found in the request parameters; redirect to
                # specified URL or to CAS logout if URL was not provided by
                # calling function
                logger.info('user integrity check: login id is required but was not found in request.')
                if missing_login_id_redirect_url:
                    logger.debug('user integrity check: redirecting to %s' % missing_login_id_redirect_url)
                    return redirect(missing_login_id_redirect_url)
                else:
                    logger.debug('user integrity check: Logging out the user from CAS.')
                    return redirect(CAS_LOGOUT_URL)
            # User integrity check passed: tool user is the same as the Canvas user, continue
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@login_required
@require_http_methods(['GET'])
@check_user_id_integrity()
def view_course(request, canvas_course_id):
    """
    The course view checks to see if the authenticated user is already enrolled in the course.
    If not, and if shopping period is still active for the course, then the user will be
    enrolled in the course as a viewer.
    """
    if not canvas_course_id:
        return render(request, 'canvas_shopping/error.html', {'error_message': 'Sorry, this request is invalid (missing course ID).'})

    course_url = '%s/courses/%s' % (settings.CANVAS_SHOPPING['CANVAS_BASE_URL'], canvas_course_id)

    user_id = request.user.username

    # is the user already in the course?
    is_enrolled = False
    enrollments = get_canvas_enrollment_by_user('sis_user_id:%s' % user_id)
    if enrollments:
        for e in enrollments:
            logger.debug('user %s is enrolled in %d - checking against %s' % (user_id, e['course_id'], canvas_course_id))
            if e['course_id'] == int(canvas_course_id):
                is_enrolled = True
                break

    if is_enrolled is True:
        # redirect the user to the actual canvas course site
        course_url = '%s/courses/%s' % (settings.CANVAS_SHOPPING['CANVAS_BASE_URL'], canvas_course_id)
        logger.info('User %s is already enrolled in course %s - redirecting to site.' % (user_id, canvas_course_id))
        return redirect(course_url)

    else:
        canvas_course = get_canvas_course_by_canvas_id(canvas_course_id)

        if not canvas_course:
            # something's wrong with the course, and we can't proceed
            logger.error('Shopping request for non-existent Canvas course id %s' % canvas_course_id)
            return render(request, 'canvas_shopping/error.html', {'error_message': 'Sorry, the Canvas course you requested does not exist.'})

        # make sure that the course is available
        if canvas_course['workflow_state'] == 'unpublished':
            return render(request, 'canvas_shopping/error.html', {'error_message': 'Sorry, this course site has not been published by the teaching staff.'})

        if not canvas_course.get('sis_course_id'):
            return render(request, 'canvas_shopping/error.html', {'error_message': 'Sorry, this Canvas course is not associated with a Harvard course ID.'})

        # TBD: check to see if the course is public; if so, just redirect

        # TBD: check to see if the course has a public syllabus; if so, just redirect to the syllabus

        # make sure this user is eligible for shopping        
        group_ids = request.session.get('USER_GROUPS', [])
        logger.debug("groups: " + "\n".join(group_ids))

        user_can_shop = False
        shopping_role = settings.CANVAS_SHOPPING['VIEWER_ROLE']

        # make sure this is a shoppable course and that this user can shop it
        is_shoppable = False
        course_instance_id = None
        try:
            ci = CourseInstance.objects.get(pk=canvas_course['sis_course_id'])   # TODO: prefetch term and course
        except ObjectDoesNotExist:
            return render(request, 'canvas_shopping/error.html', {'error_message': 'Sorry, this Canvas course is associated with an invalid Harvard course ID.'})
        except Exception as e:
            logger.exception("Exception in fetching course using sis_course_id =%s, exception=%s" % (canvas_course['sis_course_id'], e))
            return render(request, 'canvas_shopping/error.html', {'error_message': 'Sorry, this Canvas course is associated with an invalid Harvard course ID.'})

        if ci.term.shopping_active:
            is_shoppable = True

            course_instance_id = ci.course_instance_id

            # is the user eligible to view the course?
            if is_huid(user_id):
                # any HUID holder can shop
                user_can_shop = True
                shopping_role = settings.CANVAS_SHOPPING['VIEWER_ROLE']

            else: 
                # any student can shop
                group_ids = request.session.get('USER_GROUPS', [])
                for gid in group_ids:
                    if gid.startswith('ScaleSchoolEnroll:') or group_pattern.match(gid):
                        user_can_shop = True
                        shopping_role = settings.CANVAS_SHOPPING['VIEWER_ROLE']

        else:
            logger.debug('course instance term is not active for shopping: term id %d' % ci.term.term_id)
                
        if is_shoppable is False:
            return render(request, 'canvas_shopping/not_shoppable.html', {'canvas_course': canvas_course})

        elif user_can_shop is False:
            return render(request, 'canvas_shopping/not_eligible.html', {'canvas_course': canvas_course})

        else:
            # Enroll this user as a shopper
            new_enrollee = add_canvas_section_enrollee('sis_section_id:%d' % course_instance_id, shopping_role, user_id)
            if new_enrollee:
                # success
                #return render(request, 'canvas_shopping/successfully_added.html', {'canvas_course': canvas_course, 'course_url': course_url, 'shopping_role': shopping_role, 'settings': settings.CANVAS_SHOPPING})
                return redirect(course_url)
            else:
                return render(request, 'canvas_shopping/error_adding.html', {'canvas_course': canvas_course})

@login_required
@require_http_methods(['GET'])
@check_user_id_integrity()
def remove_shopper_role(request, canvas_course_id):
    logger.debug(" In remove shopper role ")
    return remove_role(request, canvas_course_id, settings.CANVAS_SHOPPING['SHOPPER_ROLE'])

@login_required
@require_http_methods(['GET'])
@check_user_id_integrity()
def remove_viewer_role(request, canvas_course_id):
    logger.debug(" In remove viewer role ")
    return remove_role(request, canvas_course_id, settings.CANVAS_SHOPPING['VIEWER_ROLE'])
    
@login_required
@require_http_methods(['GET'])
@check_user_id_integrity()
def remove_role(request, canvas_course_id, role):
    """
    Helper method to remove the  current users's enrollment for teh specified course 
    and role (Harvard-viewer or Shopper)
    """

    logger.debug(" In remove_role role=%s" %role)
    user_id = request.user.username

    # Check for  'canvas_login_id', which  will be passed in by shop.js on the Canvas instance.  If it's not present
    # the code will skip this block and continue on. If it's present, verify that it matches the user_id in the tool.
    # If there is a mismatch, send user to pin logout (this is the current security patch, maybe modified with a better solution.)
    if request.GET.get('canvas_login_id'):

        #canvas_login_id is the 'login_id' attribute from the user profile. It is essentially the sis_user_id
        sis_user_id = request.GET.get('canvas_login_id')
        logger.debug('user in shopping tool == %s' %user_id)
        logger.debug('sis_user_id  from request == %s' %sis_user_id)

        if str(user_id) != str(sis_user_id):
            logger.error('user mismatch: user in shopping tool=%s, canvas user from request=%s. Logging out the user from pin' %(user_id,sis_user_id))
            return redirect("http://login.icommons.harvard.edu/pinproxy/logout")

    canvas_course = get_canvas_course_by_canvas_id(canvas_course_id)

    shopper_enrollment_id = None
    enrollments = get_canvas_enrollment_by_user('sis_user_id:%s' % user_id)
    if enrollments:
        for e in enrollments:
            if e['course_id'] == int(canvas_course_id):
                if e['role'] == role:
                    shopper_enrollment_id = e['id']
    
    if canvas_course_id and shopper_enrollment_id:
        delete_canvas_enrollee_id(int(canvas_course_id), int(shopper_enrollment_id))
        logger.debug('viewer enrollment id %s for user %s in course %s removed' % (shopper_enrollment_id, user_id, canvas_course_id))
    
    # Return  canvas_course  object, as it's attribute(s) will be used in the confirmation page
    # return canvas_course
    course_url = '%s/courses/%s' % (settings.CANVAS_SHOPPING['CANVAS_BASE_URL'], canvas_course_id)

    return render(request, 'canvas_shopping/removal_confirmation.html', {'canvas_course': canvas_course, 'course_url': course_url})


'''
The shop_course view checks to see if the authenticated user is already enrolled in the course.
If not, and if shopping period is still active for the course, then the user will be
enrolled in the course as a shopper.
'''

@login_required
@require_http_methods(['GET'])
@check_user_id_integrity()
def shop_course(request, canvas_course_id):
    # is the user already in the course in a non-viewer role? If so, just redirect them to the course
    # if the user is already a viewer, store that record so we can remove it later and replace it with shopper

    if not canvas_course_id:
        logger.debug('no canvas course id provided!')
        return render(request, 'canvas_shopping/error.html', {'message': 'Sorry, this request is invalid (missing course ID).'})

    course_url = '%s/courses/%s' % (settings.CANVAS_SHOPPING['CANVAS_BASE_URL'], canvas_course_id)

    user_id = request.user.username

    canvas_course = get_canvas_course_by_canvas_id(canvas_course_id)

    # make sure this user is eligible for shopping
    group_ids = request.session.get('USER_GROUPS', [])
    logger.debug("groups: " + "\n".join(group_ids))

    user_can_shop = False
    shopping_role = settings.CANVAS_SHOPPING['SHOPPER_ROLE']

    # make sure this is a shoppable course and that this user can shop it
    is_shoppable = False
    course_instance_id = None
    try:
        ci = CourseInstance.objects.get(pk=canvas_course['sis_course_id'])   # TODO: prefetch term and course
    except ObjectDoesNotExist:
        return render(request, 'canvas_shopping/error.html', {'error_message': 'Sorry, this Canvas course is associated with an invalid Harvard course ID.'})

    if ci.term.shopping_active:
        is_shoppable = True

    course_instance_id = ci.course_instance_id

    # any student can shop
    group_id = None
    for gid in group_ids:
        if gid.startswith('ScaleSchoolEnroll:') or group_pattern.match(gid):
            group_id = gid
            user_can_shop = True

    if user_can_shop:
        logger.debug('User %s is eligible for shopping as a member of %s' % (user_id, group_id))  
            
    if is_shoppable is False:
        logger.debug('The course %s is not shoppable' % canvas_course_id)
        return render(request, 'canvas_shopping/not_shoppable.html', {'canvas_course': canvas_course})
    elif user_can_shop is False:
        logger.debug('User %s cannot shop this course %s' % (user_id, canvas_course_id))
        return render(request, 'canvas_shopping/not_eligible.html', {'canvas_course': canvas_course})
    else:
        # Enroll this user as a shopper
        new_enrollee = add_canvas_section_enrollee('sis_section_id:%d' % course_instance_id, shopping_role, user_id)
        if new_enrollee:
            # success
            logger.debug('user %s successfully added to course %s' % (user_id, canvas_course_id))
            return redirect(course_url)

        else:
            logger.debug('There was an error adding user %s to course %s' % (user_id, canvas_course_id))
            return render(request, 'canvas_shopping/error_adding.html', {'canvas_course': canvas_course})



'''
The course_selfreg view allows users to be added to certain courses (specified in the settings file).  The settings also indicate what role 
the new user should have within the course.  This view will also ensure that the user has a Canvas user account. Upon successful enrollment,
it simply redirects the user to the Canvas course site.
'''



@login_required
def course_selfreg(request, canvas_course_id):

    course_url = '%s/courses/%s' % (settings.CANVAS_SHOPPING['CANVAS_BASE_URL'], canvas_course_id)

    # is the user already in the course?
    user_id = request.user.username
    is_enrolled = False
    enrollments = get_canvas_enrollment_by_user('sis_user_id:%s' % user_id)
    if enrollments:
        for e in enrollments:
            logger.debug('user %s is enrolled in %d - checking against %s' % (user_id, e['course_id'], canvas_course_id))
            if e['course_id'] == int(canvas_course_id):
                is_enrolled = True
                break

    if is_enrolled is True:
        # redirect the user to the actual canvas course site
        logger.info('User %s is already enrolled in course %s - redirecting to site.' % (user_id, canvas_course_id))
        return redirect(course_url)

    else:
        canvas_course = get_canvas_course_by_canvas_id(canvas_course_id)

        # make sure this is a self-reg course
        is_selfreg = False

        # look for selfreg courses in settings:
        selfreg_courses = settings.CANVAS_SHOPPING.get('selfreg_courses')
        if selfreg_courses is not None:
            selfreg_role = selfreg_courses.get(canvas_course_id)
            if selfreg_role:
                is_selfreg = True
        else:
            logger.warn('A user is trying to self-reg for Canvas course %s, \
                but no self-reg courses have been configured in the settings file.' % canvas_course_id)

        if is_selfreg is False:
            return render(request, 'canvas_shopping/not_selfreg.html', {'canvas_course': canvas_course})

        else:
            # Enroll this user as a shopper

            # make sure the user has a Canvas account
            canvas_user = get_canvas_user(user_id)
            if not canvas_user:
                return render(request, 'canvas_shopping/error.html', {'error_message': 'Sorry, a Canvas user account does not exist for you.'})

            # if there is a section matching the course's sis_course_id, enroll the user in that; otherwise use the default section
            if canvas_course.get('sis_course_id'):
                canvas_section = get_canvas_course_section(canvas_course['sis_course_id'])
                if canvas_section:
                    new_enrollee = add_canvas_section_enrollee(canvas_section['id'], selfreg_role, user_id)
                else:
                    new_enrollee = add_canvas_course_enrollee(canvas_course_id, selfreg_role, user_id)

            else:
                new_enrollee = add_canvas_course_enrollee(canvas_course_id, selfreg_role, user_id)

            if new_enrollee:
                # success
                return redirect(course_url)

            else:
                return render(request, 'canvas_shopping/error_selfreg.html', {'canvas_course': canvas_course})


@login_required
def my_list(request):

    # fetch the Shopper and Harvard Viewer enrollments for this user, display the list
    shopper_enrollments = get_enrollments_by_user(request.user.username, settings.CANVAS_SHOPPING['SHOPPER_ROLE'])
    viewer_enrollments = get_enrollments_by_user(request.user.username, settings.CANVAS_SHOPPING['VIEWER_ROLE'])

    all_enrollments = []
    if shopper_enrollments:
        all_enrollments = shopper_enrollments

    if viewer_enrollments:
        all_enrollments = all_enrollments + viewer_enrollments

    courses = {}
    for e in all_enrollments:
        enrollment_id = e['id']
        canvas_course_id = e['course_id']
        course = get_canvas_course_by_canvas_id(canvas_course_id)
        courses[enrollment_id] = course

    return render(request, 'canvas_shopping/my_list.html', {'courses': courses, 'canvas_base_url': settings.CANVAS_SHOPPING.get('CANVAS_BASE_URL')})


def is_huid(id):
    # if this ID is an HUID, return true; otherwise return false
    if re.match('\d{8}$', id):
        return True
    else:
        return False
