from django.conf import settings

from coursemanager.models import CourseInstance


def get_course_instance_query_set(sis_term_id, sis_account_id):
    # Exclude records that have parent_course_instance_id  set(TLT-3558) as we don't want to create sites for the
    # children; they will be associated with the parent site
    filters = {'exclude_from_isites': 0, 'term_id': sis_term_id, 'parent_course_instance_id__isnull': True}

    (account_type, account_id) = sis_account_id.split(':')
    if account_type == 'school':
        filters['course__school'] = account_id
    elif account_type == 'dept':
        filters['course__department'] = account_id
    elif account_type == 'coursegroup':
        filters['course__course_group'] = account_id

    return CourseInstance.objects.filter(**filters)


def get_course_instance_summary_data(query_set):
    total_count = query_set.count()

    # get total count and external count for CIs without a Canvas site
    query_set_without_canvas_site = query_set.filter(canvas_course_id__isnull=True)
    total_without_canvas_site_count = query_set_without_canvas_site.count()
    total_without_canvas_site_with_external_count = query_set_without_canvas_site.filter(
        sitemap__course_site__site_type_id='external'
    ).exclude(sitemap__course_site__external_id__icontains=settings.CANVAS_URL).count()

    # get total count and external count for CIs without a Canvas site AND
    # with the sync_to_canvas flag set to 0
    query_set_without_canvas_site_and_sync_to_canvas_false = query_set_without_canvas_site.filter(sync_to_canvas=0)
    total_without_canvas_site_and_sync_to_canvas_false_count = query_set_without_canvas_site_and_sync_to_canvas_false.count()
    total_without_canvas_site_and_sync_to_canvas_false_with_external_count = query_set_without_canvas_site_and_sync_to_canvas_false.filter(
        sitemap__course_site__site_type_id='external'
    ).exclude(sitemap__course_site__external_id__icontains=settings.CANVAS_URL).count()

    # get total count and external count for CIs with a Canvas site
    query_set_with_canvas_site = query_set.filter(canvas_course_id__isnull=False)
    total_with_canvas_site_count = query_set_with_canvas_site.count()
    total_with_canvas_site_with_external_count = query_set_with_canvas_site.filter(
        sitemap__course_site__site_type_id='external'
    ).exclude(sitemap__course_site__external_id__icontains=settings.CANVAS_URL).count()

    return {
        'recordsTotal': total_count,
        'recordsFiltered': total_count,
        'recordsTotalWithoutCanvasSite': total_without_canvas_site_count,
        'recordsTotalWithoutCanvasSiteWithExternal': total_without_canvas_site_with_external_count,
        'recordsTotalWithoutCanvasSiteAndSyncToCanvasFalse': total_without_canvas_site_and_sync_to_canvas_false_count,
        'recordsTotalWithoutCanvasSiteAndSyncToCanvasFalseWithExternal': total_without_canvas_site_and_sync_to_canvas_false_with_external_count,
        'recordsTotalWithCanvasSite': total_with_canvas_site_count,
        'recordsTotalWithCanvasSiteWithExternal': total_with_canvas_site_with_external_count,
    }


# TODO remove
def get_course_job_summary_data(bulk_job_id):
    data = {}
    total_count = 0
    data['recordsTotal'] = total_count
    data['recordsFiltered'] = total_count
    data['recordsComplete'] = 0
    data['recordsSuccessful'] = 0
    data['recordsFailed'] = 0
    return data
