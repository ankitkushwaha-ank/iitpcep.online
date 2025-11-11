import os
import json
import warnings
from pathlib import Path
from config import DATABASE, SYSTEM  # ✅ import DB + system config safely

# --------------------------------------------------
# 📁 BASE CONFIG
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "#%%#ew765265%$hjglgshAnkjhwhe132"

# --------------------------------------------------
# ⚙️ DEBUG & ALLOWED HOSTS
# --------------------------------------------------
# This is the MASTER switch for your environments
DEBUG = False

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "iitpcep.online",
    "www.iitpcep.online",
    "iitpcep-online.onrender.com",  # This is the correct Render domain
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

# This flag must be set to "True" in your Render environment
USE_CLOUD_SQL = True
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
    
    # SYNTAX FIX: Use triple quotes for multi-line strings
    GOOGLE_CREDENTIALS_JSON_STR = """{
  "type": "service_account",
  "project_id": "gen-lang-client-0720266398",
  "private_key_id": "4023ab8fd883cce01344357b1df3071fcf2f7ab3",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC+WAtRrC9NBgMh\\nlzmMKM3t/2q+s+PjYVn6hJ5dWjzJOzDrc+HwiXmdinvxCi0z7oLOccuQYidfRohp\\ndAstcc2sAlwJaTNFbGoHzxns8UsjBY/yKf8DNE8+DS2NtRoyvC4pvzkWLu0XH7AC\\n5oOnaGHeIdHPLllW9Dg+mh6UxTcR/uG+lizJj6saV+k9SpCYQn08fMO9my7hEBTq\\nat3ynBu9xyW03EHq4n8pWjQH7gzza/PNDEq6Eq1qH5bEnxEAKlG1UfJ+bC8DtViI\\nY8U3e13MWnS0W73fjWmMs2lW3m5YhUP44bzKpFvYTpzinhY7kIR0ESQJuPiNrWMY\\nyGxqtNVHAgMBAAECggEAAw1dYEz/B/pBmmXKF4wsW5WKn1rTtV80kEOIWJESw9u0\\nbQO5yt+7EmjyLaTPCCcNQOs3nodizNcDZysXTMsnRz7u1xXK3seeXnHjONa+48v6\\nIwhD9xSwWpt446DuT4PCx73+iw0FYnQKU5mUeqtxU+lxHr3f0xJtq0KEaZ7mw0Qu\\n0qWgKi1SpGbRkYf6yKYeuRrKsy4g8pQM5V+Kf/EzHKZ4eXk5zCUaQZN06zib0D2t\\nSfIeObl0kkQz7NGcNymd19uQtTqg6V7o7tpmLvv+iu02GEXJsfbGbPa/moXuM+s5\\nHbqCx7aq0nAVWrcYk+xbkcMvKlVob/hfdSsbskrFJQKBgQD12WFHkvOpIIDU91XJ\\nyvuzEHwBwo0qCb1zigcFRI0XMp/6uMsFZ5vBCB5dlO60tmGAhrzrnhv03E8sdOum\\n2Obxja0/cMwlLOAJV8/eX3kd6PToZ4es6A9DMRsQDSarxHzY8Cn1Xnvs/ctxRK+a\\nOtskvF8Ryx1z5ojmbQpQWkNbtQKBgQDGM/msVPcPnJMx6Eerla+X9bNjl5wnNiH3\\nGAgWri4781hkwYeun10OZsdTISQSPWiYP2oZ/UZUpeNelsAliaVNO70E54qdtHr0\\n+BQygpuW8jHHFbrpAO1noh+zhksCqFfGUrFexANfaHULHvRhl30ammbXMP8oblUU\\nG32WnqQiiwKBgCV+iKqMy+JwVZWlPw0uiuKNUgxGqpbNs3oKg/WWtdni26k2Q6hI\\nW+W9ojvtedZPtmEOq4NXsrXOX7jNAB+LFvWiANkbD9dfl691F/u3Hdak76z+FSAW\\nqDU8KP9ysgIiTlQblJqaVVYYgs18hzeDYGai3/DrxEsnzpst6BPHIFy9AoGAKUKq\\nqChr4jEbJ1mOifa4Pi8k8Aegtzz6pyC2lloeP9axwQ/UuhJs4dGdjv2oL6/e9UrG\\nQLDMElUSVx+U0nusEL7t43Z8EcZ/jj2Sns03rJ2wpRwt89GAmoFSjiHXva7jzuJq\\nECtH9HWfX/hKsYJCxeX8oLGPfJAzX+M1KsTNsG8CgYEAsz+NOxAOUlMpSPArIbzK\\nZ8VQV/Ii4G43C0bsUT0xKBJ8Tq/a+qd08oIK93K/7smkO/BhxL/01lGKOCePIdRD\\nMJ5hIVofh0AfJLEbJ00u5BnFQwhETwHqOeWN2lAywhmPI0T8osTqzEfXgLb5ELFD\\neL92uG+DJGFikbCsRnlMmw4=\\n-----END PRIVATE KEY-----\\n",
  "client_email": "iitpcep-app@gen-lang-client-0720266398.iam.gserviceaccount.com",
  "client_id": "107191285374346481100",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/iitpcep-app%40gen-lang-client-0720266398.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}"""

    if GOOGLE_CREDENTIALS_JSON_STR:
        try:
            # 👇 THIS IS THE FIX 👇
            from google.oauth2 import service_account

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
                    "gen-lang-client-0720266398:us-central1:iitpcep-instance",  # Cloud SQL instance name
                    "pymysql",
                    user="iitpcepdb_user",
                    password="Admin@admin123!@#", # <-- TODO: Add your password
                    db="iitpcep_db",
                )

            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.mysql",
                    "NAME": "django_db",
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
    GS_BUCKET_NAME = "iitpcep-bucket" # <-- TODO: Add your bucket name
    if GS_BUCKET_NAME and GS_CREDENTIALS:  # Check for both
        DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
        GS_FILE_OVERWRITE = False
        MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"
        print("[SETTINGS] Google Cloud Storage (Media) configured.")
    else:
        warnings.warn("⚠️ GS_BUCKET_NAME or credentials not set. Media will use local storage.")
        MEDIA_URL = "/media/"
        MEDIA_ROOT = os.path.join(BASE_DIR, "media")  # Fallback to local
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
