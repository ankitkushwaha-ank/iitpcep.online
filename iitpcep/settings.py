import os
import json
import warnings
from pathlib import Path
import dj_database_url  # ✅ Added for Render PostgreSQL
from config import DATABASE, SYSTEM  # ✅ import DB + system config safely

# --------------------------------------------------
# 📁 BASE CONFIG
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
# Reverted to using environment variables for safety
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-local-dev-key")

# --------------------------------------------------
# ⚙️ DEBUG & ALLOWED HOSTS
# --------------------------------------------------
# This is the MASTER switch for your environments
# Set to True to use local SQLite and local media, as you requested.
DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "iitpcep.online",
    "www.iitpcep.online",
    "iitpcep-online.onrender.com",
    "cet.iitpcep.online",
]

# Add Render's internal host pattern to allowed hosts automatically
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    "https://iitpcep.online",
    "https://www.iitpcep.online",
    "https://iitpcep-online.onrender.com",
    "https://cet.iitpcep.online",
]

LOGIN_URL = 'admin_dashboard:admin_login'
LOGIN_REDIRECT_URL = 'admin_dashboard:admin_dashboard'
# --------------------------------------------------
# 🧩 INSTALLED APPS
# --------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Your apps
    "moodle",
    "admin_dashboard",

    # 3rd Party Apps
    "ckeditor",
    "storages",  # for Google Cloud Storage
]

# --------------------------------------------------
# ⚙️ MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Should be near the top
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "moodle.middleware.SystemStatusMiddleware",
]

# --------------------------------------------------
# 🌐 URL + WSGI
# --------------------------------------------------
ROOT_URLCONF = "iitpcep.urls"
WSGI_APPLICATION = "iitpcep.wsgi.application"

# --------------------------------------------------
# 🎨 TEMPLATES
# --------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "moodle", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "iitpcep.settings.system_context",
                "moodle.context_processors.global_user_context",
            ],
        },
    },
]

# --------------------------------------------------
# 📦 DATABASE, STATIC & MEDIA SETTINGS
# --------------------------------------------------

print("--------------------------------------------------")
print(f"[SETTINGS] Environment: {'Render/Production' if os.environ.get('DATABASE_URL') else 'Development'}")
print(f"[SETTINGS] System Online: {SYSTEM.get('SYSTEM_ON', True)}")
print("--------------------------------------------------")

# 1. Database Configuration
# Default to SQLite (Local)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Render PostgreSQL Override
# If DATABASE_URL environment variable exists (Render provides this), overwrite with Postgres
database_url = os.environ.get("DATABASE_URL")
if database_url:
    DATABASES["default"] = dj_database_url.config(
        default=database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
    print("[SETTINGS] Using Database: PostgreSQL (Render)")
else:
    print("[SETTINGS] Using Database: SQLite (Local)")


# 2. Static Files (Kept exactly as you requested)
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "moodle", "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles_dev")
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# 3. Media Files (Kept exactly as you requested - Local Storage Only)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# --------------------------------------------------
# 🧾 DEFAULT PRIMARY KEY FIELD
# --------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------
# 🌐 GLOBAL CONTEXT PROCESSOR
# --------------------------------------------------
def system_context(request):
    """Inject SYSTEM settings globally into templates"""
    return {"SYSTEM": SYSTEM}