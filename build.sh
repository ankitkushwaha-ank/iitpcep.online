#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install Requirements
pip install -r requirements.txt

# 2. Collect Static Files
python manage.py collectstatic --no-input

# 3. Migrate Database (Ensure tables exist)
python manage.py migrate

# 4. Flush Old Data (⚠️ DELETES ALL EXISTING DATA ON RENDER)
# This solves the "Duplicate key" error by removing the existing "Ankit"
python manage.py flush --no-input

# 5. Load New Data
python manage.py loaddata data.json

#render's build command
#pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate