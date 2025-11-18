import os
import dj_database_url
from pathlib import Path

# Import config safely; if it fails, we continue with defaults
try:
    from config import DATABASE, SYSTEM
except ImportError:
    DATABASE = {}
    SYSTEM = {"SYSTEM_ON": True}

# --------------------------------------------------
# 📁 BASE CONFIG
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-local-dev-key")

# --------------------------------------------------
# ⚙️ DEBUG & ALLOWED HOSTS
# --------------------------------------------------
# Default to False in production. Only True if explicitly set to "True".
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "iitpcep.online",
    "www.iitpcep.online",
    "iitpcep-online.onrender.com",
    "cet.iitpcep.online",
    ".onrender.com",  # Allow all render subdomains
]

CSRF_TRUSTED_ORIGINS = [
    "https://iitpcep.online",
    "https://www.iitpcep.online",
    "https://iitpcep-online.onrender.com",
    "https://cet.iitpcep.online",
]

LOGIN_URL = "/admincp/login/"
LOGIN_REDIRECT_URL = "/admincp/"
LOGOUT_REDIRECT_URL = "/admincp/login/"

# --------------------------------------------------
# 🧩 INSTALLED APPS
# --------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # This is CRITICAL for collectstatic:
    "django.contrib.staticfiles",

    # Your apps
    "moodle",
    "admin_dashboard",

    # 3rd Party Apps
    "ckeditor",
    "storages",
]

# --------------------------------------------------
# ⚙️ MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
if DEBUG:
    print(f"[SETTINGS] Environment: Development (DEBUG=True)")

    # Local SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    print("[SETTINGS] Environment: Production (DEBUG=False)")

    # Render PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=True
        )
    }

    # Fallback if DATABASE_URL is missing (prevents crash during build if DB isn't ready)
    if not DATABASES['default']:
        print("⚠️ WARNING: DATABASE_URL not found. Using SQLite fallback.")
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
    else:
        print("[SETTINGS] Render PostgreSQL configured.")

# --- Static Files (Always same logic for simplicity) ---
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "moodle", "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
# Use Whitenoise for storage
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Media Files (GCS or Local) ---
GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
GOOGLE_CREDENTIALS_JSON_STR = os.getenv("GOOGLE_CREDENTIALS_JSON")

# Check if we have everything needed for Google Cloud Storage
use_gcs = not DEBUG and GS_BUCKET_NAME and GOOGLE_CREDENTIALS_JSON_STR

if use_gcs:
    try:
        import json
        from google.oauth2 import service_account

        info = json.loads(GOOGLE_CREDENTIALS_JSON_STR)
        GS_CREDENTIALS = service_account.Credentials.from_service_account_info(info)

        DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
        GS_FILE_OVERWRITE = False
        MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"
        print("[SETTINGS] Google Cloud Storage (Media) configured.")

    except Exception as e:
        print(f"⚠️ ERROR initializing GCS: {e}")
        use_gcs = False

if not use_gcs:
    # Local Media Fallback
    print("[SETTINGS] Using Local Media Storage.")
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

print("--------------------------------------------------")

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