from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from icommons_common.canvas_utils import *
from django.conf import settings
from canvas_shopping.decorators import check_user_id_integrity
import logging
import json
import re

group_pattern = re.compile('LdapGroup:[a-z]+\.student')

logger = logging.getLogger(__name__)


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
    if not canvas_course:
        # something's wrong with the course, and we can't proceed
        logger.error('Shopping request for non-existent Canvas course id %s' % canvas_course_id)
        return render(request, 'canvas_shopping/error.html', {'error_message': 'Sorry, the Canvas course you requested does not exist.'})


    # make sure this user is eligible for shopping
    group_ids = request.session.get('USER_GROUPS', [])
    logger.debug("groups: " + "\n".join(group_ids))

    user_can_shop = False
    shopping_role = settings.CANVAS_SHOPPING['SHOPPER_ROLE']

    # make sure this is a shoppable course and that this user can shop it
    is_shoppable = False
    course_instance_id = None

    # only lookup the course if we have a valid canvas course
    
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
 This method checks if the user is eligible for shopping. It returns a boolean value based on this check
'''
@login_required
@require_http_methods(['GET'])
@check_user_id_integrity()
def is_shoppable_user(request):
    user_can_shop = False
    user_id = request.user.username

    # Fetch the user groups that are loaded in the session for this user and check for the presence of
    # scale enrollment group or LDAP student group 
    group_ids = request.session.get('USER_GROUPS', [])
    logger.debug("groups: " + "\n".join(group_ids))
    for gid in group_ids:
        if gid.startswith('ScaleSchoolEnroll:') or group_pattern.match(gid):
            user_can_shop = True
            #break on the first occurance
            break

    data = json.dumps({'is_shoppable_user': user_can_shop ,'user': user_id})   
    logger.debug('Returning data = %s for user=%s' % (data,user_id)) 
    return HttpResponse(data, content_type="application/json")

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
@require_http_methods(['GET'])
@check_user_id_integrity()
def my_list(request):

    # fetch the Shopper enrollments for this user, display the list
    shopper_enrollments = get_enrollments_by_user(request.user.username, settings.CANVAS_SHOPPING['SHOPPER_ROLE'])

    all_enrollments = shopper_enrollments if shopper_enrollments else []

    courses = {}
    for e in all_enrollments:
        enrollment_id = e['id']
        canvas_course_id = e['course_id']
        course = get_canvas_course_by_canvas_id(canvas_course_id)
        courses[enrollment_id] = course

    return render(request, 'canvas_shopping/my_list.html',
                  {'courses': courses, 'canvas_base_url': settings.CANVAS_SHOPPING['CANVAS_BASE_URL']})


@login_required
@require_http_methods(['POST'])
def remove_shopper_ui(request):
    """
    This method is called from the my_list page to remove shopper status from a specific course.
    Does not need @check_user_id_integrity() as it should never be called from Canvas.
    """
    canvas_course_id = request.POST.get('canvas_course_id')
    canvas_enrollee_id = request.POST.get('canvas_enrollee_id')

    if canvas_course_id and canvas_enrollee_id:
        delete_canvas_enrollee_id(int(canvas_course_id), int(canvas_enrollee_id))
        messages.success(request, 'Successfully updated your shopping list.')
    else:
        messages.error(request, 'Could not update your shopping list. Please try again later')

    response = redirect(reverse('sh:my_list'))
    # my_list view requires the canvas login ID as it can be called from Canvas directly
    # and needs to be sure it's operating on the correct logged-in user
    # TODO: this may be removed if the security check is capable of distinguishing local and remote requests
    response['Location'] += '?canvas_login_id=%s' % request.user.username
    return response


def is_huid(id):
    # if this ID is an HUID, return true; otherwise return false
    if re.match('\d{8}$', id):
        return True
    else:
        return False
