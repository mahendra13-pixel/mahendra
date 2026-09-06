#!/bin/bash
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Create superuser using environment variables
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser --noinput
fi