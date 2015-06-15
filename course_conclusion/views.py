from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(['GET'])
def index(request):
    return render(request, 'course_conclusion/index.html', {})
