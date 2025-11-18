import os
import json
import warnings
import dj_database_url  # <--- 1. ADDED THIS IMPORT
from pathlib import Path
from config import DATABASE, SYSTEM  # ✅ import DB + system config safely

# --------------------------------------------------
# 📁 BASE CONFIG
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-local-dev-key")

# --------------------------------------------------
# ⚙️ DEBUG & ALLOWED HOSTS
# --------------------------------------------------
# ⭐ 2. MADE DEBUG DYNAMIC
# Set DJANGO_DEBUG="True" locally, and "False" in Render
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "iitpcep.online",
    "www.iitpcep.online",
    "iitpcep-online.onrender.com",  # This is the correct Render domain
    "cet.iitpcep.online",
]
# ... (rest of your file from CSRF_TRUSTED_ORIGINS to TEMPLATES) ...
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

# ⭐ 3. UN-COMMENTED THE IF/ELSE BLOCK
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

    # --- 2. CONFIGURE DATABASE (Render PostgreSQL) ---
    # This automatically reads the 'DATABASE_URL' env variable
    # that Render provides.
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,    # How long connections persist
            ssl_require=True     # Force SSL for security
        )
    }
    print("[SETTINGS] Render PostgreSQL configured.")


    # --- 3. CONFIGURE STATIC FILES (Whitenoise) ---
    STATIC_URL = "/static/"
    STATICFILES_DIRS = [os.path.join(BASE_DIR, "moodle", "static")]
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

    # --- 4. CONFIGURE MEDIA FILES (Your choice: GCS, R2, etc.) ---
    # (Leaving your GCS logic here, as you only asked to update the DB)
    credentials = None
    GS_CREDENTIALS = None
    GOOGLE_CREDENTIALS_JSON_STR = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if GOOGLE_CREDENTIALS_JSON_STR:
        try:
            from google.oauth2 import service_account
            info = json.loads(GOOGLE_CREDENTIALS_JSON_STR)
            credentials = service_account.Credentials.from_service_account_info(info)
            GS_CREDENTIALS = credentials
        except Exception as e:
            warnings.warn(f"CRITICAL Error loading Google credentials: {e}")
    else:
        warnings.warn("CRITICAL WARNING: 'GOOGLE_CREDENTIALS_JSON' env var not set.")

    GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
    if GS_BUCKET_NAME and GS_CREDENTIALS:
        DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
        GS_FILE_OVERWRITE = False
        MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"
        print("[SETTINGS] Google Cloud Storage (Media) configured.")
    else:
        warnings.warn("⚠️ GS_BUCKET_NAME or credentials not set. Media will use local storage.")
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