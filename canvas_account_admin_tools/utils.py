import json
import logging

from course_info.canvas import get_administered_school_accounts

from canvas_sdk.exceptions import CanvasAPIError

logger = logging.getLogger(__name__)


def _get_schools_context(canvas_user_id):
    accounts = get_administered_school_accounts(canvas_user_id)
    schools = [{
                    'key': 'school',
                    'value': a['sis_account_id'].split(':')[1],
                    'name': a['name'],
                    'query': True,
                    'text': a['name'] + ' <span class="caret"></span>',
                } for a in accounts]
    schools = sorted(schools, key=lambda s: s['name'].lower())
    return json.dumps(schools)

