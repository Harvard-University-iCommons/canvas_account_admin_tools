from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'icommons_tools.db.sqlite3',
    },
}
# DATABASE_ROUTERS = ['icommons_common.routers.DatabaseAppsRouter']
# DATABASE_APPS_MAPPING = {
#     'canvas_whitelist': 'default',
#     'icommons_common': 'default',
#     'icommons_ui': 'default',
#     'isites_export_tool': 'default',
#     'qualtrics_whitelist': 'default',
#     'term_tool': 'default',
# }
# DATABASE_MIGRATION_WHITELIST = ['default']


EXPORT_TOOL = {
    'base_file_download_url': 'https://qa.isites.harvard.edu/exports/',
    'ssh_hostname': 'icommons@qa.isites.harvard.edu',  # name used to connect via ssh to perl script server
    'ssh_private_key': '/home/vagrant/.ssh/id_rsa',
    'create_site_zip_cmd': '/u02/icommons/perlapps/iSitesAPI/scripts/export_site_files_zip.pl',
    'remove_site_zip_cmd': '/u02/icommons/perlapps/iSitesAPI/scripts/rm_export_file.pl',
    'archive_cutoff_time_in_hours': 2,  # express cutoff time in hours
    'archive_task_crontab_hours': "*/1",  # hourly frequency that periodic task executes in crontab format
    'allowed_groups': 'IcGroup:358',
    'local_archive_dir': 'logs'
}
