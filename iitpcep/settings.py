import os
from pathlib import Path
import dj_database_url

# --------------------------------------------------
# 🔒 Safe Import (from config.py)
# --------------------------------------------------
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
# ⚙️ DEBUG & HOSTS
# --------------------------------------------------
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "iitpcep.online",
    "www.iitpcep.online",
    "iitpcep-online.onrender.com",
    "cet.iitpcep.online",
    ".onrender.com",
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
    "cloudinary_storage",       # ✅ Must be before staticfiles
    "django.contrib.staticfiles",
    "moodle",
    "admin_dashboard",
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
# 🎨 TEMPLATE CONFIG
# --------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "moodle" / "templates"],
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
# 🧾 DATABASE CONFIG
# --------------------------------------------------
print("--------------------------------------------------")
if DEBUG:
    print("[SETTINGS] Environment: DEVELOPMENT")

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    print("[SETTINGS] Environment: PRODUCTION")
    DATABASES = {
        "default": dj_database_url.config(conn_max_age=600, ssl_require=True)
    }

    if not DATABASES.get("default"):
        print("⚠️ DATABASE_URL not found. Using SQLite fallback.")
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }

# --------------------------------------------------
# 🧱 STATIC FILES
# --------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "moodle" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Whitenoise will serve static files efficiently
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"


# --------------------------------------------------
# ☁️ MEDIA STORAGE (Cloudinary)
# --------------------------------------------------
CLOUDINARY_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "dexyu0v8j")
CLOUDINARY_KEY = os.getenv("CLOUDINARY_API_KEY", "225798755461141")
CLOUDINARY_SECRET = os.getenv("CLOUDINARY_API_SECRET", "<your_api_secret_here>")

if CLOUDINARY_SECRET and CLOUDINARY_KEY:
    print("[SETTINGS] ✅ Cloudinary connected.")
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": CLOUDINARY_NAME,
        "API_KEY": CLOUDINARY_KEY,
        "API_SECRET": CLOUDINARY_SECRET,
        "SECURE": True,
    }
else:
    print("⚠️ Cloudinary not configured — using local media fallback.")
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------
# 🧾 DEFAULT FIELD TYPE
# --------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------
# 🌍 GLOBAL CONTEXT PROCESSOR
# --------------------------------------------------
def system_context(request):
    """Inject SYSTEM settings globally into templates"""
    return {"SYSTEM": SYSTEM}

print(f"[SETTINGS] Media Storage: {DEFAULT_FILE_STORAGE}")
print("--------------------------------------------------")
