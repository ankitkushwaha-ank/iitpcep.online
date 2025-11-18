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

    # Cloudinary Storage must be before django.contrib.staticfiles
    "cloudinary_storage",

    "django.contrib.staticfiles",

    # Your apps
    "moodle",
    "admin_dashboard",

    # 3rd Party Apps
    "ckeditor",
    "cloudinary",
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
# 📦 DATABASE SETTINGS
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

    # Fallback if DATABASE_URL is missing
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

# --------------------------------------------------
# 📦 STATIC FILES (CSS/JS)
# --------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "moodle", "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Use Whitenoise for storage
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# CRITICAL FIX FOR RENDER BUILD:
# This allows the build to succeed even if CKEditor references a missing image file.
WHITENOISE_MANIFEST_STRICT = False

# --------------------------------------------------
# ☁️ MEDIA FILES (CLOUDINARY)
# --------------------------------------------------
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "<your_api_secret_here>")

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dexyu0v8j',
    'API_KEY': '225798755461141',
    'API_SECRET': CLOUDINARY_API_SECRET,
    'SECURE': True,
    'MEDIA_TAG': 'media',
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

print(f"[SETTINGS] Cloudinary Storage Configured for Cloud Name: {CLOUDINARY_STORAGE['CLOUD_NAME']}")

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