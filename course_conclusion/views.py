from django.shortcuts import render


def index(request):
    return render(request, 'course_conclusion/index.html', {})
