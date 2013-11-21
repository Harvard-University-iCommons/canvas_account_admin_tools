from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from ims_lti_py.tool_provider import DjangoToolProvider

from time import time
import logging

logger = logging.getLogger(__name__)

# Create your views here.


def index(request):

    return render('index.html')

