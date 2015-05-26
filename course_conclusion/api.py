import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from icommons_common.models import School


@login_required
@require_http_methods(['GET'])
def schools(request):
    query = School.objects.filter(active=1)

    # filter down to just the user's allowed schools if the user isn't an admin
    if not user_is_admin(request):
        query = query.filter(school_id__in=user_allowed_schools)

    school_data = [{'school_id': school.school_id,
                    'title_short': school.title_short} for school in query]
    return HttpResponse(json.dumps(school_data),
                        content_type='application/json',
                        status=200)


def user_is_admin(request):
    user_groups = set(request.session['USER_GROUPS'])
    admin_group = set()
    if 'ADMIN_GROUP' in settings.TERM_TOOL:
        admin_group.add(settings.TERM_TOOL['ADMIN_GROUP'])
    return bool(admin_group & user_groups)


def user_allowed_schools(request):
    user_groups = set(request.session['USER_GROUPS'])
    allowed_by_group = settings.TERM_TOOL.get('ALLOWED_GROUPS', {})
    user_allowed_groups = user_groups.intersection(allowed_by_group.keys())
    return [school for group, school in allowed_by_group
                if group in user_allowed_groups]
