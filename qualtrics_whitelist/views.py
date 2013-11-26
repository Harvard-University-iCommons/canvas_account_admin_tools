from django.shortcuts import render
from django.views import generic
from icommons_common.models import *


import logging

logger = logging.getLogger(__name__)

### Class-based views:

class QualtricsAccessListView(generic.ListView):
	model = QualtricsAccessList
	template_name = 'qualtrics_whitelist/qualtrics_access_list.html' 
	context_object_name = 'qualtrics_access_list'
	queryset = QualtricsAccessList.objects.all()

#class PersonView(generic.ListView):
#	model = Person
#	template_name = 'qualtrics_whitelist/qualtrics_access_list.html'
#	context_object_name = 'qualtrics_access_list'
#	queryset = Person.objects.filter()


