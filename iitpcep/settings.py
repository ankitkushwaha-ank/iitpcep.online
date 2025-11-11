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
# This is the MASTER switch for your environments
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "iitpcep.online",
    "www.iitpcep.online",
    "iitpcep-online.onrender.com", # This is the correct Render domain
    "cet.iitpcep.online",
    # "https-iitpcep-online.onrender.com", # This was invalid and removed
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
    "whitenoise.middleware.WhiteNoiseMiddleware", # Should be near the top
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

# This flag must be set to "True" in your Render environment
USE_CLOUD_SQL = os.getenv("USE_CLOUD_SQL", "False") in ("1", "true", "True")

if DEBUG:
    # --- 🌞 DEVELOPMENT SETTINGS ---
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

else:
    # --- 🚀 PRODUCTION SETTINGS ---
    print("--------------------------------------------------")
    print("[SETTINGS] Environment: Production")
    print(f"[SETTINGS] System Online: {SYSTEM.get('SYSTEM_ON', True)}")
    print("--------------------------------------------------")

    # --- 1. LOAD CREDENTIALS (FOR DB & STORAGE) ---
    credentials = None
    GS_CREDENTIALS = None  # <-- This is required for django-storages
    GOOGLE_CREDENTIALS_JSON_STR = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if GOOGLE_CREDENTIALS_JSON_STR:
        try:
            info = json.loads(GOOGLE_CREDENTIALS_JSON_STR)
            credentials = service_account.Credentials.from_service_account_info(info)
            GS_CREDENTIALS = credentials  # <-- Pass credentials to django-storages
        except Exception as e:
            warnings.warn(f"CRITICAL Error loading Google credentials: {e}")
    else:
        warnings.warn("CRITICAL WARNING: 'GOOGLE_CREDENTIALS_JSON' env var not set.")

    # --- 2. CONFIGURE DATABASE ---
    if USE_CLOUD_SQL:
        print("[SETTINGS] Attempting to use Google Cloud SQL...")
        try:
            import pymysql
            from cloud_sql_python_connector import connector

            # Fix for PyMySQL
            pymysql.version_info = (1, 4, 6)
            pymysql.install_as_MySQLdb()

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
            print("[SETTINGS] Google Cloud SQL configured.")

        except ModuleNotFoundError:
            warnings.warn("⚠️ cloud_sql_python_connector not installed. Falling back.")
            DATABASES = {"default": DATABASE if DATABASE else {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
    else:
        print("[SETTINGS] USE_CLOUD_SQL is False. Using fallback database.")
        DATABASES = {"default": DATABASE if DATABASE else {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

    # --- 3. CONFIGURE STATIC FILES (Whitenoise) ---
    STATIC_URL = "/static/"
    STATICFILES_DIRS = [os.path.join(BASE_DIR, "moodle", "static")]
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

    # --- 4. CONFIGURE MEDIA FILES (Google Cloud Storage) ---
    GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
    if GS_BUCKET_NAME and GS_CREDENTIALS: # Check for both
        DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
        GS_FILE_OVERWRITE = False
        MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"
        print("[SETTINGS] Google Cloud Storage (Media) configured.")
    else:
        warnings.warn("⚠️ GS_BUCKET_NAME or credentials not set. Media will use local storage.")
        MEDIA_URL = "/media/"
        MEDIA_ROOT = os.path.join(BASE_DIR, "media") # Fallback to local
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
