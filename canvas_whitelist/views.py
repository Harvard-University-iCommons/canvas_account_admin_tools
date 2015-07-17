from django.shortcuts import render
from django.views import generic
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.contrib import messages
from icommons_common.models import Person, CanvasAccessList
from icommons_common.auth.views import LoginRequiredMixin
from icommons_common.auth.views import GroupMembershipRequiredMixin
from icommons_common.auth.decorators import group_membership_restriction
from django.contrib.auth.decorators import login_required
from django.conf import settings

from canvas_sdk.methods import users
from canvas_sdk import RequestContext
from requests import HTTPError

import logging

logger = logging.getLogger(__name__)

request_context = RequestContext(settings.CANVAS_WHITELIST.get('oauth_token'), settings.CANVAS_WHITELIST.get('canvas_url'))

@login_required
@group_membership_restriction(allowed_groups=settings.CANVAS_WHITELIST.get('allowed_groups', ''))
def delete(request):
    if request.method == 'POST':
        id_delete = request.POST.get('id')
        
        if 'cancel' in request.POST:
            logger.warning("Now canceling and returning")
        else:
            logger.debug('now deleting %s' % id_delete)
            delete_id = CanvasAccessList.objects.get(id=id_delete).delete()
            logger.info('Whitelist delelte successful id delete: %s' % delete_id)
            messages.success(request, "Whitelist delete user successful")
    return HttpResponseRedirect(reverse('cwl:canvasaccesslist'))
    

@login_required
@group_membership_restriction(allowed_groups=settings.CANVAS_WHITELIST.get('allowed_groups', ''))
def access_update_person(request):
    logger.debug('trying to update now/////////')
    id_update = request.POST.get('id')
    if 'cancel' in request.POST:
        logger.warning("Now canceling")
    else:
        wlistSave = CanvasAccessList()
        wlistSave.id = id_update
        logger.debug('Trying to update id :%s:' % id_update)
        user_id = request.POST.get('user_id')
        wlistSave.user_id = user_id
        test_description = request.POST.get('description')
        test_description = test_description.strip()
        # Verify the length and truncate to max length 255, if exceeds 255 chars
        # database max length for description is 255, but just need 150 for reason description
        if len(test_description) > 150:
            wlistSave.description = test_description[:150]
            messages.info(request, "The Reason Description is too long, it has been shortened to 150 characters.")
        else:
            wlistSave.description = test_description
        wlistSave.version = 0
        # Check the expiration_date date, if not "None", save to the database
        # if "None", save None to the database
        saveAs_expiration_date = request.POST.get('expiration_date')
       
        if saveAs_expiration_date == "None" or len(saveAs_expiration_date) == 0:
            wlistSave.expiration_date = None
        else:
            wlistSave.expiration_date = saveAs_expiration_date
       
        try:
            wlistSave.save()
            messages.success(request, "Whitelist update user successful")

            # now add the user to Canvas so they'll be available immediately
            try:
                results = users.get_user_profile(request_context, 'sis_user_id:%s' % user_id)
                print 'results status: %d' % results.status_code
                if results.status_code == 200:
                    logger.info('Canvas user already exists for user_id %s' % user_id)

            except HTTPError as e:

                if e.response.status_code == 404:
                    # go ahead and create the user
                    logger.info('Canvas user does not already exist for userid %s - will create one' % user_id)

                    try:
                        personlist = Person.objects.filter(univ_id=user_id)
                        if personlist and len(personlist) > 0:
                            person = personlist[0]
                            user_name = '%s %s' % (person.name_first, person.name_last)
                            new_canvas_user = users.create_user(request_context, account_id='1', 
                                                                user_name=user_name, 
                                                                pseudonym_unique_id=user_id, 
                                                                user_time_zone='America/New_York', 
                                                                pseudonym_sis_user_id=user_id, 
                                                                pseudonym_send_confirmation=False, 
                                                                communication_channel_address=person.email_address,
                                                                communication_channel_skip_confirmation=True)                     
                    except:
                        logger.error('Failed to create a Canvas user for user_id %s' % user_id)   

            except:
                logger.error('Some other error occurred when trying to fetch the Canvas user profile')

        except IntegrityError, e:
            logger.error('Exception raised while saving to database:%s (%s)' % (e.args[0], type(e)))
            messages.error(request, "Whitelist update/deleted failed")

    return HttpResponseRedirect(reverse('cwl:canvasaccesslist'))


# Mixins:
# Class-based views:

class CanvasAccessListView(GroupMembershipRequiredMixin, generic.ListView):
    allowed_groups = settings.CANVAS_WHITELIST.get('allowed_groups', '')
    model = CanvasAccessList
    template_name = 'canvas_whitelist/canvas_access_list.html' 
    context_object_name = 'canvas_access_list'
    input_user_id = ""

    # override get_context to filter by name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CanvasAccessListView, self).get_context_data(**kwargs)
        alist = []
        all_whitelist = CanvasAccessList.objects.all()  # return all the objects from the WL table
        for wlobj in all_whitelist:
            alist.append(wlobj.user_id)

        personlist = Person.objects.filter(univ_id__in=alist)
        
        # print personlist.query  # print out SQL query

        for wlist in all_whitelist:
            for plist in personlist:
                if wlist.user_id == plist.univ_id:
                    wlist.name_first = plist.name_first
                    wlist.name_last = plist.name_last
                    wlist.email_address = plist.email_address
                    if plist.role_type_cd == 'XIDHOLDER':
                        wlist.role_type = 'XID'
                    else:
                        wlist.role_type = 'HUID'
                        break

        context['canvas_access_list'] = all_whitelist
        context['AUTHORIZEDTOEDIT'] = True

        return context      


class CanvasAccessSearchView(GroupMembershipRequiredMixin, generic.TemplateView):
    allowed_groups = settings.CANVAS_WHITELIST.get('allowed_groups', '')
    template_name = 'canvas_whitelist/canvas_access_search.html'


class CanvasAccessResultsListView(GroupMembershipRequiredMixin, generic.ListView):
    allowed_groups = settings.CANVAS_WHITELIST.get('allowed_groups', '')
    model = CanvasAccessList
    template_name = 'canvas_whitelist/canvas_access_results_list.html'
    context_object_name = 'canvas_access_list'

    def post(self, request, *args, **kwargs):
        error_message = ""
        firstname = lastname = ""
        results_dict = {}
        search_term = request.POST.get('user_search_term')
        if 'Search' in request.POST:
            search_term = search_term.strip()
            if "@" in search_term:
                # treat it as an email address     
                personlist = Person.objects.filter(email_address__iexact=search_term)

                if personlist:
                    # person found on ldap_people_plus_simple model
                    for plist in personlist:
                        input_user_id = plist.univ_id 

                        q = CanvasAccessList.objects.all().filter(user_id=plist.univ_id)
                        if q:
                                
                            for qlist in q:
                                if plist.univ_id == qlist.user_id:
                                    qlist.on_list = True
                                else:
                                    qlist.on_list = False
                        else:
                            # exist on Person object, but not on whitelist database
                            qlist = CanvasAccessList(user_id=plist.univ_id)
                            qlist.on_list = False

                        # display either HUID or XID as the Role Type in UI
                        if plist.role_type_cd == 'XIDHOLDER':
                            qlist.role_type = 'XID'
                        else:
                            qlist.role_type = 'HUID'

                        qlist.user_id = plist.univ_id
                        qlist.first_name = plist.name_first 
                        qlist.last_name = plist.name_last
                        qlist.email = plist.email_address

                        results_dict[qlist.user_id] = qlist
                            
                    return render(request, 'canvas_whitelist/canvas_access_results_list.html', 
                                      {'user_input': input_user_id, 'results_list': results_dict, 'error_message': "", })
                    
                else:
                    # person not found in Person database
                    logger.error('Email not found in Person database :%s:' % search_term)
                    return render(request, 'canvas_whitelist/canvas_access_results_list.html', 
                                  {'user_input': search_term, 'results_list': results_dict, 'error_message': "Person not found in the Harvard Directory", })

            else:
                # treat it as a user id
                if not len(search_term) <= 0:
                    alist = []
                    qlist = CanvasAccessList.objects.all().filter(user_id=search_term)  # return all the objects from the WL table

                    if qlist:
                        # User already exist on whitelist
                        for wlobj in qlist:
                            alist.append(wlobj.user_id)

                        personlist = Person.objects.filter(univ_id__in=alist)                    
                        for wlist in qlist:
                            for plist in personlist:
                                if wlist.user_id == plist.univ_id:
                                    wlist.first_name = plist.name_first
                                    wlist.last_name = plist.name_last
                                    wlist.email = plist.email_address
                                    wlist.on_list = True
                                    if plist.role_type_cd == 'XIDHOLDER':
                                        wlist.role_type = 'XID'
                                    else:
                                        wlist.role_type = 'HUID'
                                    results_dict[wlist.user_id] = wlist
                    else:
                        # User is not on the whitelist
                        personlist = Person.objects.filter(univ_id=search_term)

                        for plist in personlist:
                            plist.user_id = plist.univ_id
                            plist.first_name = plist.name_first
                            plist.last_name = plist.name_last
                            plist.email = plist.email_address
                            plist.on_list = False
                            if plist.role_type_cd == 'XIDHOLDER':
                                plist.role_type = 'XID'
                            else:
                                plist.role_type = 'HUID' 
                            results_dict[plist.user_id] = plist

                        if len(results_dict) == 0:
                            logger.error("This person doesn't exist in the Person database.")
                            messages.warning(request, "Person does not exist in the Harvard Directory")
                            return HttpResponseRedirect(reverse('cwl:access_searchfor'))
                        
                        return render(request, 'canvas_whitelist/canvas_access_results_list.html', 
                                    {'user_input': search_term, 'results_list': results_dict, 'error_message': error_message, })
                                        
        elif 'Cancel' in request.POST:
            return HttpResponseRedirect(reverse('cwl:canvasaccesslist'))

        elif 'Save' in request.POST:
            input_user_id = request.POST.get('user_id')
            # Look-up the person in the Harvard Directory
            personlist = Person.objects.filter(univ_id=input_user_id)
            if personlist:
                for plist in personlist:
                    firstname = plist.name_first 
                    lastname = plist.name_last
                    break
            input_check_list = request.POST.getlist('user_check_list')  

            test_description = request.POST.get('description')
            test_description = test_description.strip()
            # Verify the length and truncate to max length 255, if exceeds 255 chars
            # database max length for description is 255, but just need 150 for reason description
            if len(test_description) > 150:
                input_description = test_description[:150]
                messages.info(request, "The Reason Description is too long, it has been shorten to 150 characters.")
            else:
                input_description = test_description

            input_expiration_date = request.POST.get('expiration_date')
            if input_expiration_date == "None" or len(input_expiration_date) == 0:
                input_expiration_date = None

            if not input_check_list:
                error_message = "At least one row must be checked"
                logger.error('Nothing checked to update')
                messages.error(request, "Whitelist update/deleted failed")

            else:

                for user_id in input_check_list:
                    # when multi-select, re-initialize to reset QUALTRICS_ACESS_LIST.ID to none, so that 
                    # the auto-trigger will select the next number in the sequence, if not, no rows 
                    # will be updated with the same QUALTRICS_ACESS_LIST.ID from the previous insert
                    wlistSave = CanvasAccessList()
                    wlistSave.user_id = user_id
                    wlistSave.description = input_description
                    wlistSave.version = 0
                    wlistSave.expiration_date = input_expiration_date

                    try:
                        wlistSave.save()
                        messages.success(request, "%s %s, (%s), has been successfully added to the whitelist" % (firstname, lastname, wlistSave.user_id))

                        # now add the user to Canvas so they'll be available immediately
                        try:
                            results = users.get_user_profile(request_context, 'sis_user_id:%s' % user_id)
                            print 'results status: %d' % results.status_code
                            if results.status_code == 200:
                                logger.info('Canvas user already exists for user_id %s' % user_id)

                        except HTTPError as e:

                            if e.response.status_code == 404:
                                # go ahead and create the user
                                logger.info('Canvas user does not already exist for userid %s - will create one' % user_id)

                                try:
                                    personlist = Person.objects.filter(univ_id=user_id)
                                    if personlist and len(personlist) > 0:
                                        person = personlist[0]
                                        user_name = '%s %s' % (person.name_first, person.name_last)
                                        new_canvas_user = users.create_user(request_context, account_id='1', 
                                                                            user_name=user_name, 
                                                                            pseudonym_unique_id=user_id, 
                                                                            user_time_zone='America/New_York', 
                                                                            pseudonym_sis_user_id=user_id, 
                                                                            pseudonym_send_confirmation=False, 
                                                                            communication_channel_address=person.email_address,
                                                                            communication_channel_skip_confirmation=True)                     
                                except:
                                    logger.error('Failed to create a Canvas user for user_id %s' % user_id)   

                        except:
                            logger.error('Some other error occurred when trying to fetch the Canvas user profile')

                        
                    except IntegrityError, e:
                        logger.error('Exception raised while saving to database:%s (%s)' % (e.args[0], type(e)))
                        messages.error(request, "Whitelist add user failed")

            return HttpResponseRedirect(reverse('cwl:canvasaccesslist'))

        return render(request, 'canvas_whitelist/canvas_access_results_list.html', 
                      {'user_input': search_term, 'results_list': results_dict, 'error_message': error_message})


class CanvasAccessEditView(GroupMembershipRequiredMixin, generic.UpdateView):
    allowed_groups = settings.CANVAS_WHITELIST.get('allowed_groups', '')
    model = CanvasAccessList
    template_name = 'canvas_whitelist/canvas_access_edit.html'
    context_object_name = 'canvas_access_edit'

    def get_object(self):
        wlobject = super(CanvasAccessEditView, self).get_object()
        
        personList = Person.objects.filter(univ_id=wlobject.user_id)
        
        for plist in personList:
            wlobject.first_name = plist.name_first
            wlobject.last_name = plist.name_last
            wlobject.email_address = plist.email_address
        
        return wlobject


class CanvasAccessConfirmDeleteView(GroupMembershipRequiredMixin, generic.DetailView):
    allowed_groups = settings.CANVAS_WHITELIST.get('allowed_groups', '')
    """docstring for CanvasAccessConfirmDeleteView"""
    model = CanvasAccessList
    template_name = 'canvas_whitelist/canvas_access_confirmdelete.html'
    queryset = CanvasAccessList.objects.all()

    def get_object(self):
        wlobject = super(CanvasAccessConfirmDeleteView, self).get_object()
        
        personList = Person.objects.filter(univ_id=wlobject.user_id)
        
        for plist in personList:
            wlobject.first_name = plist.name_first
            wlobject.last_name = plist.name_last
            wlobject.email_address = plist.email_address
        
        return wlobject
