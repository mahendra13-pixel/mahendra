#!/bin/bash
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Check if superuser exists before creating
if ! python manage.py shell -c "from django.contrib.auth import get_user_model; import sys; sys.exit(0 if get_user_model().objects.filter(username='admin').exists() else 1)"; then
    python manage.py createsuperuser --noinput
    echo "Superuser created successfully!"
else
    echo "Superuser already exists - skipping creation"
fi