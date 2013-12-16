from django.shortcuts import render
from django.views import generic
from django.template import RequestContext
from django.core.context_processors import csrf
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse_lazy
from django.core.urlresolvers import reverse
from icommons_common.models import *
from itertools import chain
from icommons_common.models import Person
# from app.forms import Form1, Form2

import logging

logger = logging.getLogger(__name__)


### Mixins:




### Class-based views:

class QualtricsAccessListView(generic.ListView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_list.html' 
	context_object_name = 'qualtrics_access_list'
	input_user_id = ""
	# form_class = Form1
	# second_form_class = Form2
	success_url = reverse_lazy("success")
	# queryset = QualtricsAccessList.objects.all()

	# override get_context to filter by name
	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		context = super(QualtricsAccessListView, self).get_context_data(**kwargs)
		alist = []
		all_whitelist = QualtricsAccessList.objects.all()  ## return all the objects from the WL table
		for wlobj in all_whitelist:
			alist.append(wlobj.user_id)
	
		for item in alist:
			print item

		personlist = Person.objects.filter(univ_id__in=alist)
		
		#print personlist.query  # print out SQL query

		for wlist in all_whitelist:
			for plist in personlist:
				if wlist.user_id == plist.univ_id:
					wlist.name_first = plist.name_first
					wlist.name_last = plist.name_last
					if plist.role_type_cd == 'XIDHOLDER':
						wlist.role_type = 'XID'
					else:
						wlist.role_type = 'HUID'
						break

		context['qualtrics_access_list'] = all_whitelist
		return context		

	def post(self, request, *args, **kwargs):
		
		
 #        # determine which form is being submitted
 #        # uses the name of the form's submit button
		if 'updateForm' in request.POST:
 			
 			print "Update now"
 #            # get the primary form
 #            # form_class = self.get_form_class()
 #            # form_name = 'updateForm'
 
		elif 'deleteForm' in request.POST:
 
			print "delete now"
 #            # get the secondary form
 #            # form_class = self.second_form_class
 #            # form_name = 'deleteForm'

		return HttpResponse("update/delete successful")

        



class QualtricsAccessSearchView(generic.CreateView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_search.html'
	queryset = QualtricsAccessList.objects.none()




class QualtricsAccessResultsListView(generic.ListView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_results_list.html'
	context_object_name = 'qualtrics_access_list'

	def post(self, request, *args, **kwargs):
		print "Now in the dangerzone"
		error_message = ""
		results_list = []
		if request.method == 'POST':
			if 'Search' in request.POST:
				input_user_id = request.POST.get('search_by_huid')
				print input_user_id
				input_email = request.POST.get('search_by_email')
				

				if not len(input_user_id) <= 0:
					alist = []
					# results_list = []
					qlist = QualtricsAccessList.objects.all().filter(user_id=input_user_id)  ## return all the objects from the WL table

					if qlist:
						print "User already exist on whitelist============="
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
							print "User is not on the whitelist"
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
					print "checking for email now"
					print input_email
					personlist = Person.objects.filter(email_address__contains=input_email)
					if personlist:
						print "not empty"
						for plist in personlist:
							plist.univ_id = input_user_id
							print plist.univ_id
							q = QualtricsAccessList.objects.all().filter(user_id=input_user_id)
							if plist.univ_id == q.user_id:
								q.on_list = True
							else:
								q.on_list = False
							plist.name_first = q.first_name
							plist.name_last = q.last_name
							plist.email_address = q.email
							results_list.append(q)
							return render(request, 'qualtrics_whitelist/qualtrics_access_results_list.html', {'user_input' : input_user_id, 'results_list' : results_list, 'error_message': "",})
					
					else:
						print "empty personlist"

					


			elif 'Cancel' in request.POST:
				print "now trying to cancel and return to home page"
				return HttpResponseRedirect('../../qualtrics_whitelist/')
			elif 'Save' in request.POST:
				print "now in Save"
				input_user_id =  request.POST.get('user_id')
				input_list = request.POST.get('users_list')
				input_user_list = request.POST.getlist('access_user_id_list')

				if not input_user_list:
					print "Empty List"
					error_message = "Nothing to update"
					results_list = input_list 
					
				else:
					print "Updating now and return to home page"
					for user in input_user_list:
						print user
					return HttpResponseRedirect('../../qualtrics_whitelist/')

		return render(request, 'qualtrics_whitelist/qualtrics_access_results_list.html', {'user_input' : input_user_id, 'results_list' : results_list, 'error_message' : error_message } )

		# def Cancel(request):
		# 	print "Trying to cancel"
		# 	return redirect('qualtrics_whitelist/qualtrics_access_list.html')

# class NamedRedirectView(RedirectView):
#     url_name = None

#     def get_redirect_url(self, *args, **kwargs):
#     	return super(NamedRedirectView, self).get_redirect_url(**kwargs)
        # if self.url_name:
        #     return reverse(url_name)
        # return super(NamedRedirectView, self).get_redirect_url(**kwargs)

# class RedirectView(RedirectView):

# 	def get_redirect_url(self, *args, **kwargs):
# 		print "you are in RedirectView now"
# 		return super(RedirectView, self).get_redirect_url(*args, **kwargs)


	# # override get_context to filter by name
	# def get_context_data(self, **kwargs):
	# 	# Call the base implementation first to get a context
	# 	# context = super(QualtricsAccessResultsListView, self).get_context_data(**kwargs)

	# 	plist = Person.objects.filter(univ_id__in=request.POST.get('search_huid'))
		
	# 	print "Getting context now ##########"
	# 	kwargs['results_list'] = plist
	# 	return super(QualtricsAccessResultsListView, self).get_context_data(**kwargs)



class QualtricsAccessEditView(generic.UpdateView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_edit.html'
	# queryset = QualtricsAccessList.objects.none()
	context_object_name = 'qualtrics_access_add'


	# override get_context to filter by name
	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		context = super(QualtricsAccessListView, self).get_context_data(**kwargs)


class QualtricsAccessAddView(generic.CreateView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_add.html'


class QualtricsAccessDeleteView(generic.DeleteView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_delete.html'



