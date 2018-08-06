web: gunicorn -c gunicorn.py canvas_account_admin_tools.wsgi:application
rq: python manage.py rqworker bulk_publish_canvas_sites
bulk_course_settings: python manage.py process_bulk_course_settings_jobs --job-limit 100