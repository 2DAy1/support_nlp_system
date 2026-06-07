#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate

if [ "$SEED_DEMO_DATA" = "True" ]; then
    python manage.py seed_demo_data
fi
