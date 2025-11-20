import os
import json
import warnings
from pathlib import Path
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

# This flag is no longer needed for local-only setup
# USE_CLOUD_SQL = True

# if DEBUG:
# --- 🌞 DEVELOPMENT SETTINGS ---
# This block is now ACTIVE because DEBUG = True
print("--------------------------------------------------")
print(f"[SETTINGS] Environment: Development")
print(f"[SETTINGS] Using Database Engine: SQLite")
print(f"[SETTINGS] System Online: {SYSTEM.get('SYSTEM_ON', True)}")
print("--------------------------------------------------")

# Local SQLite
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Local Static Files
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "moodle", "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles_dev")
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Local Media Files
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
#old settings.py on m