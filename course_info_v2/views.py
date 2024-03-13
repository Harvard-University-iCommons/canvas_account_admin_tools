import logging

from django.shortcuts import render

logger = logging.getLogger(__name__)


def index(request):
    return render(request, "course_info_v2/course_search.html", {})


def details(request):
    return render(request, "course_info_v2/course_details.html", {})
