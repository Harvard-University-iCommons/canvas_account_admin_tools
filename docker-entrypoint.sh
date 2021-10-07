#!/bin/sh

./python_venv/bin/python3 manage.py migrate                  # Apply database migrations
./python_venv/bin/python3 manage.py collectstatic --noinput  # Collect static files

# Start Gunicorn processes
echo Starting Gunicorn.
exec ./python_venv/bin/gunicorn -c canvas_account_admin_tools/settings/gunicorn.conf.py canvas_account_admin_tools.wsgi:application