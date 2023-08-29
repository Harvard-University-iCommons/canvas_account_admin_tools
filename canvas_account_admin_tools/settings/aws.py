from .base import *
from logging.config import dictConfig

# tlt hostnames
ALLOWED_HOSTS = ['.tlt.harvard.edu']
ALLOWED_CIDR_NETS = [SECURE_SETTINGS.get('vpc_cidr_block')]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECURE_SETTINGS['django_secret_key']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# AWS Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
EMAIL_USE_TLS = True
# Amazon Elastic Compute Cloud (Amazon EC2) throttles email traffic over port 25 by default.
# To avoid timeouts when sending email through the SMTP endpoint from EC2, use a different
# port (587 or 2587)
EMAIL_PORT = 587
EMAIL_HOST_USER = SECURE_SETTINGS.get('email_host_user', '')
EMAIL_HOST_PASSWORD = SECURE_SETTINGS.get('email_host_password', '')

# Store static files in S3
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = SECURE_SETTINGS.get('static_files_s3_bucket')
AWS_QUERYSTRING_AUTH = False
AWS_LOCATION = SECURE_SETTINGS.get('static_files_s3_prefix')
AWS_DEFAULT_ACL = None

# SSL is terminated at the ELB so look for this header to know that we should be in ssl mode
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True

CANVAS_EMAIL_NOTIFICATION_TEST_MODE = SECURE_SETTINGS.get('canvas_email_notification_test_mode', False)

if CANVAS_EMAIL_NOTIFICATION_TEST_MODE:
    CANVAS_EMAIL_NOTIFICATION['course_migration_success_subject'] += ' (TEST, PLEASE IGNORE)'
    CANVAS_EMAIL_NOTIFICATION['course_migration_failure_subject'] += ' (TEST, PLEASE IGNORE)'
    CANVAS_EMAIL_NOTIFICATION['support_email_subject_on_failure'] += ' (TEST, PLEASE IGNORE)'
    CANVAS_EMAIL_NOTIFICATION['support_email_address'] = 'tltqaemails@g.harvard.edu'


# Make sure we send logs to Splunk in production (default handler 
# is configured for logging to Splunk).
LOGGING['handlers']['default']['filters'].append('require_debug_false')
# make sure dictConfig(LOGGING) stays at the bottom of the file
dictConfig(LOGGING)
