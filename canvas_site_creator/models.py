from django.conf import settings

from icommons_common.models import CourseInstance

from canvas_course_site_wizard.models import CanvasCourseGenerationJob


def get_course_instance_query_set(sis_term_id, sis_account_id):
    filters = {'exclude_from_isites': 0, 'term_id': sis_term_id}

    (account_type, account_id) = sis_account_id.split(':')
    if account_type == 'school':
        filters['course__school'] = account_id
    elif account_type == 'dept':
        filters['course__departments'] = account_id
    elif account_type == 'coursegroup':
        filters['course__course_groups'] = account_id

    return CourseInstance.objects.filter(**filters)


def get_course_instance_summary_data(query_set):
    total_count = query_set.count()

    query_set_without_canvas_site = query_set.filter(canvas_course_id__isnull=True)
    total_without_canvas_site_count = query_set_without_canvas_site.count()
    total_without_canvas_site_with_isites_count = query_set_without_canvas_site.filter(
        sitemap__course_site__site_type_id='isite'
    ).count()
    total_without_canvas_site_with_external_count = query_set_without_canvas_site.filter(
        sitemap__course_site__site_type_id='external'
    ).exclude(sitemap__course_site__external_id__icontains=settings.CANVAS_URL).count()

    query_set_with_canvas_site = query_set.filter(canvas_course_id__isnull=False)
    total_with_canvas_site_count = query_set_with_canvas_site.count()
    total_with_canvas_site_with_isites_count = query_set_with_canvas_site.filter(
        sitemap__course_site__site_type_id='isite'
    ).count()
    total_with_canvas_site_with_external_count = query_set_with_canvas_site.filter(
        sitemap__course_site__site_type_id='external'
    ).exclude(sitemap__course_site__external_id__icontains=settings.CANVAS_URL).count()

    return {
        'recordsTotal': total_count,
        'recordsFiltered': total_count,
        'recordsTotalWithoutCanvasSite': total_without_canvas_site_count,
        'recordsTotalWithoutCanvasSiteWithISite': total_without_canvas_site_with_isites_count,
        'recordsTotalWithoutCanvasSiteWithExternal': total_without_canvas_site_with_external_count,
        'recordsTotalWithCanvasSite': total_with_canvas_site_count,
        'recordsTotalWithCanvasSiteWithISite': total_with_canvas_site_with_isites_count,
        'recordsTotalWithCanvasSiteWithExternal': total_with_canvas_site_with_external_count,
    }


def get_course_job_summary_data(bulk_job_id):
    data = {}
    total_count = CanvasCourseGenerationJob.objects.filter(bulk_job_id=bulk_job_id).count()
    data['recordsTotal'] = total_count
    data['recordsFiltered'] = total_count
    data['recordsComplete'] = CanvasCourseGenerationJob.objects.filter_complete(bulk_job_id=bulk_job_id).count()
    data['recordsSuccessful'] = CanvasCourseGenerationJob.objects.filter_successful(bulk_job_id=bulk_job_id).count()
    data['recordsFailed'] = CanvasCourseGenerationJob.objects.filter_failed(bulk_job_id=bulk_job_id).count()
    return data
