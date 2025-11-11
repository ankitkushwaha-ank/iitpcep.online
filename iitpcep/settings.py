import os
import json
import warnings
from pathlib import Path
from config import DATABASE, SYSTEM  # ✅ import DB + system config safely

# --------------------------------------------------
# 📁 BASE CONFIG
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-your-secret-key")

# --------------------------------------------------
# ⚙️ DEBUG & ALLOWED HOSTS
# --------------------------------------------------
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "iitpcep.online",
    "www.iitpcep.online",
    "iitpcep-online.onrender.com",
    "https-iitpcep-online.onrender.com",
    "cet.iitpcep.online",
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

USE_CLOUD_SQL = os.getenv("USE_CLOUD_SQL", "False") in ("1", "true", "True")

if DEBUG:
    print("--------------------------------------------------")
    print(f"[SETTINGS] Environment: Development")
    print(f"[SETTINGS] Using Database Engine: SQLite")
    print(f"[SETTINGS] System Online: {SYSTEM.get('SYSTEM_ON', True)}")
    print(f"[SETTINGS] Base Directory: {BASE_DIR}")
    print("--------------------------------------------------")

    # Local SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

    STATIC_URL = "/static/"
    STATICFILES_DIRS = [os.path.join(BASE_DIR, "moodle", "static")]
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles_dev")
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

else:
    print("--------------------------------------------------")
    print("[SETTINGS] Environment: Production")
    print(f"[SETTINGS] System Online: {SYSTEM.get('SYSTEM_ON', True)}")
    print("--------------------------------------------------")

    # Default fallback database (Render PostgreSQL / MySQL via DATABASE_URL)
    DATABASES = {
        "default": DATABASE
        if DATABASE and isinstance(DATABASE, dict)
        else {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

    # Optional Google Cloud SQL setup
    if USE_CLOUD_SQL:
        try:
            import pymysql
            from google.oauth2 import service_account
            from cloud_sql_python_connector import connector

            GOOGLE_CREDENTIALS_JSON_STR = os.getenv("GOOGLE_CREDENTIALS_JSON")
            credentials = None

            if GOOGLE_CREDENTIALS_JSON_STR:
                info = json.loads(GOOGLE_CREDENTIALS_JSON_STR)
                credentials = service_account.Credentials.from_service_account_info(info)
            else:
                warnings.warn("⚠️ GOOGLE_CREDENTIALS_JSON not found.")

            db_connector = connector.Connector(credentials=credentials)

            def get_db_conn():
                return db_connector.connect(
                    os.getenv("DB_HOST", ""),  # Cloud SQL instance name
                    "pymysql",
                    user=os.getenv("DB_USER", ""),
                    password=os.getenv("DB_PASS", ""),
                    db=os.getenv("DB_NAME", ""),
                )

            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.mysql",
                    "NAME": os.getenv("DB_NAME"),
                    "CONN_CALLABLE": get_db_conn,
                }
            }

        except ModuleNotFoundError:
            warnings.warn(
                "⚠️ cloud_sql_python_connector not installed. Using fallback SQLite."
            )
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": BASE_DIR / "db.sqlite3",
                }
            }

    # Static files for production (Whitenoise)
    STATIC_URL = "/static/"
    STATICFILES_DIRS = [os.path.join(BASE_DIR, "moodle", "static")]
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

    # Google Cloud Storage (optional for media)
    DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
    GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
    GS_FILE_OVERWRITE = False
    MEDIA_URL = (
        f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"
        if GS_BUCKET_NAME
        else "/media/"
    )

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
