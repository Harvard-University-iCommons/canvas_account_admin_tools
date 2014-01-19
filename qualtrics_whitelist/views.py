from django.shortcuts import render
from django.views import generic
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.contrib import messages
from icommons_common.models import *
from icommons_common.models import Person
from icommons_common.auth.views import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

import logging

logger = logging.getLogger(__name__)

@login_required
def delete(request):
	if request.method == 'POST':
		id_delete = request.POST.get('id')
		
		if 'cancel' in request.POST:
			logger.warning("Now canceling and returning")
		else:
			logger.debug ('now deleting %s' % id_delete)
			delete_id = QualtricsAccessList.objects.get(id=id_delete).delete()
			messages.success(request, "Whitelist delete user successful")
	return HttpResponseRedirect(reverse('qwl:qualtricsaccesslist'))
	
@login_required
def access_update_person(request):
	logger.debug ('trying to update now/////////')
	id_update = request.POST.get('id')
	if 'cancel' in request.POST:
		logger.warning("Now canceling and returning")
	else:
		wlistSave = QualtricsAccessList()
		wlistSave.id = id_update
		logger.debug ('Trying to update id :%s:' % id_update)
		user = request.POST.get('user_id')
		wlistSave.user_id = user
		wlistSave.description = request.POST.get('description')
		wlistSave.version = 0
		# wlistSave.access_end_date = request.POST.get('access_end_date')
		try:
			wlistSave.save()
			messages.success(request, "Whitelist update user successful")
		except IntegrityError, e:
			logger.error ('Exception raised while saving to database:%s (%s)' % (e.args[0], type (e)))
			messages.error(request, "Whitelist update/deleted failed")

	return HttpResponseRedirect(reverse('qwl:qualtricsaccesslist'))

### Mixins:




### Class-based views:

class QualtricsAccessListView(LoginRequiredMixin, generic.ListView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_list.html' 
	context_object_name = 'qualtrics_access_list'
	input_user_id = ""

	# override get_context to filter by name
	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		context = super(QualtricsAccessListView, self).get_context_data(**kwargs)
		alist = []
		all_whitelist = QualtricsAccessList.objects.all()  ## return all the objects from the WL table
		for wlobj in all_whitelist:
			alist.append(wlobj.user_id)

		personlist = Person.objects.filter(univ_id__in=alist)
		
		#print personlist.query  # print out SQL query

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

		context['qualtrics_access_list'] = all_whitelist
		return context		



class QualtricsAccessSearchView(LoginRequiredMixin, generic.CreateView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_search.html'
	queryset = QualtricsAccessList.objects.none()


class QualtricsAccessResultsListView(LoginRequiredMixin, generic.ListView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_results_list.html'
	context_object_name = 'qualtrics_access_list'

	def post(self, request, *args, **kwargs):
		error_message = ""
		results_list = []
		if request.method == 'POST':
			if 'Search' in request.POST:
				input_user_id = request.POST.get('search_by_huid')
				input_email = request.POST.get('search_by_email')

				if not len(input_user_id) <= 0:
					alist = []
					qlist = QualtricsAccessList.objects.all().filter(user_id=input_user_id)  ## return all the objects from the WL table

					if qlist:
						# print "User already exist on whitelist============="
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
									results_list.append(wlist)
					else:
						# print "User is not on the whitelist"
						personlist = Person.objects.filter(univ_id=input_user_id)

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
							results_list.append(plist)	

							return render(request, 'qualtrics_whitelist/qualtrics_access_results_list.html', {'user_input' : input_user_id, 'results_list' : results_list, 'error_message': "User id not on the whitelist.",})
				
				elif input_email:

					personlist = Person.objects.filter(email_address__iexact=input_email)

					if personlist:
						# person found on ldap_people_plus_simple model
						for plist in personlist:
							input_user_id = plist.univ_id 

							q = QualtricsAccessList.objects.all().filter(user_id=plist.univ_id)
							if q:
								
								for qlist in q:
									if plist.univ_id == qlist.user_id:
										qlist.on_list = True
									else:
										qlist.on_list = False
							else:
								# exist on Person object, but not on whitelist database
								qlist = QualtricsAccessList(user_id=plist.univ_id)
								qlist.on_list = False

							if plist.role_type_cd == 'XIDHOLDER':
								qlist.role_type = 'XID'
							else:
								qlist.role_type = 'HUID'
							qlist.user_id = plist.univ_id
							qlist.first_name = plist.name_first 
							qlist.last_name = plist.name_last
							qlist.email = plist.email_address
							results_list.append(qlist)
							
						return render(request, 'qualtrics_whitelist/qualtrics_access_results_list.html', {'user_input' : input_user_id, 'results_list' : results_list, 'error_message': "",})
					
					else:
						# person not found in Person database
						logger.error ('Email not found in Person database :%s:' % input_email)
						return render(request, 'qualtrics_whitelist/qualtrics_access_results_list.html', {'user_input' : input_user_id, 'results_list' : results_list, 'error_message': "Person not found in database",})
										

			elif 'Cancel' in request.POST:
				return HttpResponseRedirect(reverse('qwl:qualtricsaccesslist'))

			elif 'Save' in request.POST:
				input_user_id =  request.POST.get('user_id')
				input_list = request.POST.get('users_list')
				input_check_list = request.POST.getlist('user_check_list')				
				input_description = request.POST.get('description')

				input_access_end_date = request.POST.get('access_end_date')

				if not input_check_list :
					error_message = "At least one row must be checked"
					logger.error ('Nothing checked to update')
					messages.error(request, "Whitelist update/deleted failed")

				else:
					wlistSave = QualtricsAccessList()

					for user in input_check_list:
						wlistSave.user_id = user
						wlistSave.description = input_description
						wlistSave.version = 0
						try:
							wlistSave.save()
							messages.success(request, "Whitelist add user successful")
						except IntegrityError, e:
							logger.error ('Exception raised while saving to database:%s (%s)' % (e.args[0], type (e)))
							messages.error(request, "Whitelist add user failed")
					return HttpResponseRedirect(reverse('qwl:qualtricsaccesslist'))

		return render(request, 'qualtrics_whitelist/qualtrics_access_results_list.html', {'user_input' : input_user_id, 'results_list' : results_list, 'error_message' : error_message } )


class QualtricsAccessEditView(LoginRequiredMixin, generic.UpdateView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_edit.html'
	context_object_name = 'qualtrics_access_edit'


	def get_object(self):
		wlobject = super(QualtricsAccessEditView, self).get_object()
		
		personList = Person.objects.filter(univ_id=wlobject.user_id)
		
		for plist in personList:
			wlobject.first_name = plist.name_first
			wlobject.last_name = plist.name_last
			wlobject.email_address = plist.email_address
		
		return wlobject


class QualtricsAccessConfirmDeleteView(LoginRequiredMixin, generic.DetailView):
	"""docstring for QualtricsAccessConfirmDeleteView"""
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_confirmdelete.html'
	queryset = QualtricsAccessList.objects.all()

	def get_object(self):
		wlobject = super(QualtricsAccessConfirmDeleteView, self).get_object()
		
		personList = Person.objects.filter(univ_id=wlobject.user_id)
		
		for plist in personList:
			wlobject.first_name = plist.name_first
			wlobject.last_name = plist.name_last
			wlobject.email_address = plist.email_address
		
		return wlobject

	

	

