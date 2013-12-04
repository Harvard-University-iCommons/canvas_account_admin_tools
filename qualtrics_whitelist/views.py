from django.shortcuts import render
from django.views import generic
from django.template import RequestContext
from django.core.context_processors import csrf
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from icommons_common.models import *
from itertools import chain
from icommons_common.models import Person

import logging

logger = logging.getLogger(__name__)


### Mixins:




### Class-based views:

class QualtricsAccessListView(generic.ListView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_list.html' 
	context_object_name = 'qualtrics_access_list'
	# queryset = QualtricsAccessList.objects.all()

	# def get_queryset(self):
	# 	return QualtricsAccessList.objects.all()

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
					break

		# for name in personlist:
		# 	print name.univ_id
		# 	print name.name_first

		context['qualtrics_access_list'] = all_whitelist
		return context


		
		



class QualtricsAccessSearchView(generic.CreateView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_search.html'

	def get_queryset(self):
		return QualtricsAccessList.objects.none()


	def post(self, request, *args, **kwargs):
		print "hello world!!!!!!!!!!"
		if request.method == 'POST':
			print "we are here"
			access_user_id = request.POST.get('search_huid')
			print access_user_id
			if access_user_id:
				render(request, 'qualtrics_whitelist/qualtrics_access_results_list.html')
			else:
				return render(request, 'qualtrics_whitelist/qualtrics_access_search.html')


class QualtricsAccessResultsListView(generic.ListView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_results_list.html'
	context_object_name = 'qualtrics_access_list'

	def post(self, request, *args, **kwargs):
		print "Now in the dangerzone"
		# context = super(QualtricsAccessResultsListView, self).get_context_data(**kwargs)
		if request.method == 'POST':
			access_user_id = request.POST.get('search_huid')
			print access_user_id
			#plist = Person.objects.filter(univ_id=access_user_id)
			#plist = QualtricsAccessList.objects.filter(user_id=access_user_id)
			# context['results_list'] = plist
			alist = []
			qlist = QualtricsAccessList.objects.all().filter(user_id=access_user_id)  ## return all the objects from the WL table

			for wlobj in qlist:
				alist.append(wlobj.user_id)

			personlist = Person.objects.filter(univ_id__in=alist)

			for item in personlist:
				print item

			print "I'm here now!!!!"

			
			for wlist in qlist:
				for plist in personlist:
					if wlist.user_id == plist.univ_id:
						wlist.name_first = plist.name_first
						wlist.name_last = plist.name_last
						

		return render(request, 'qualtrics_whitelist/qualtrics_access_results_list.html', {'user_input' : access_user_id, 'results_list' : wlist})


	# override get_context to filter by name
	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		# context = super(QualtricsAccessResultsListView, self).get_context_data(**kwargs)

		plist = Person.objects.filter(univ_id__in=request.POST.get('search_huid'))
		
		print "Getting context now ##########"
		kwargs['results_list'] = plist
		return super(QualtricsAccessResultsListView, self).get_context_data(**kwargs)



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



