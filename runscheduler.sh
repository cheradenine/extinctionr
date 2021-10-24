#!/bin/bash

export PYTHONPATH=/home/src/extinctionr/

source /home/xr/xrboston.org/venv/bin/activate

export DEBUG='false'
export DJANGO_SETTINGS_MODULE=extinctionr.prod_settings

python manage.py runreminders
