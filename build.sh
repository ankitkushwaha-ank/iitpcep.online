#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install Requirements
pip install -r requirements.txt

# 2. Collect Static Files
python manage.py collectstatic --no-input

# 3. Migrate Database (Create tables)
python manage.py migrate

# 4. Load Your Data (The new part)
# ⚠️ WARNING: This overwrites data with matching IDs!
python manage.py loaddata data.json

#render's build command
#pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate