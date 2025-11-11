import os
from pathlib import Path
from config import DATABASE, SYSTEM  # ✅ import DB + system config safely
import json
import warnings # For production warnings

# --------------------------------------------------
# 📁 BASE CONFIG
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key')

# --------------------------------------------------
# ⚙️ DEBUG & ALLOWED HOSTS
# --------------------------------------------------
# This is the MASTER switch.
# Set DJANGO_DEBUG = "True" in your local environment
# Set DJANGO_DEBUG = "False" in Render/Railway
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'iitpcep.online', 'www.iitpcep.online', 'https-iitpcep-online.onrender.com', 'iitpcep-online.onrender.com', 'cet.iitpcep.online']
CSRF_TRUSTED_ORIGINS = [
    'https://iitpcep.online',
    'https://www.iitpcep.online',
    'https://iitpcep-online.onrender.com',
    'https://cet.iitpcep.online', # Added https://
]

# Redirect Django login checks
LOGIN_URL = "/admincp/login/"
LOGIN_REDIRECT_URL = "/admincp/"
LOGOUT_REDIRECT_URL = "/admincp/login/"

# --------------------------------------------------
# 🧩 INSTALLED APPS
# --------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Your apps
    'moodle',
    "admin_dashboard",
    
    # 3rd Party Apps
    "ckeditor",
    "storages",  # <-- REQUIRED for Google Cloud Storage
]

# --------------------------------------------------
# ⚙️ MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Whitenoise middleware should be near the top
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'moodle.middleware.SystemStatusMiddleware',
]

# --------------------------------------------------
# 🌐 URL + WSGI
# --------------------------------------------------
ROOT_URLCONF = 'iitpcep.urls'
WSGI_APPLICATION = 'iitpcep.wsgi.application'

# --------------------------------------------------
# 🎨 TEMPLATES
# --------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'moodle', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'iitpcep.settings.system_context',
                'moodle.context_processors.global_user_context',
            ],
        },
    },
]

# --------------------------------------------------
# 📦 DYNAMIC SETTINGS (DB, STATIC, MEDIA)
# --------------------------------------------------

if DEBUG:
    # --- DEVELOPMENT SETTINGS (DEBUG = True) ---
    print("--------------------------------------------------")
    print(f"[SETTINGS] Environment: Development")
    print(f"[SETTINGS] Using Database Engine: SQLite")
    print(f"[SETTINGS] System Online: {SYSTEM.get('SYSTEM_ON', True)}")
    print(f"[SETTINGS] Base Directory: {BASE_DIR}")
    print("--------------------------------------------------")

    # Database: Local SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

    # Static Files: Local
    STATIC_URL = '/static/'
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'moodle', 'static')]
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_dev')
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

    # Media Files: Local
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

else:
    # --- PRODUCTION SETTINGS (DEBUG = False) ---
    print("--------------------------------------------------")
    print("[SETTINGS] Environment: Production")
    print(f"[SETTINGS] System Online: {SYSTEM.get('SYSTEM_ON', True)}")
    print("--------------------------------------------------")

    # --- Imports moved INSIDE the 'else' block ---
    import pymysql
    from google.oauth2 import service_account
    from cloud_sql_python_connector import connector

    # --- Load Google Credentials ---
    credentials = None
    GS_CREDENTIALS = None
    GOOGLE_CREDENTIALS_JSON_STR = os.environ.get('GOOGLE_CREDENTIALS_JSON')

    if GOOGLE_CREDENTIALS_JSON_STR:
        try:
            info = json.loads(GOOGLE_CREDENTIALS_JSON_STR)
            credentials = service_account.Credentials.from_service_account_info(info)
            GS_CREDENTIALS = credentials
        except Exception as e:
            warnings.warn(f"CRITICAL Error loading Google credentials: {e}")
    else:
        warnings.warn("CRITICAL WARNING: 'GOOGLE_CREDENTIALS_JSON' env var not set.")

    # --- Cloud SQL (MySQL) Production Config ---
    pymysql.version_info = (1, 4, 6)
    pymysql.install_as_MySQLdb()
    
    db_connector = connector.Connector(credentials=credentials)

    def get_db_conn():
        conn = db_connector.connect(
            os.environ.get('DB_HOST', ''),  # 'project:region:instance'
            "pymysql",
            user=os.environ.get('DB_USER', ''),
            password=os.environ.get('DB_PASS', ''),
            db=os.environ.get('DB_NAME', ''),
        )
        return conn

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME'),
            'CONN_CALLABLE': get_db_conn,
        }
    }

    # --- Production Static Files (Whitenoise) ---
    STATIC_URL = '/static/'
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'moodle', 'static')]
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

    # --- Production Media Files (Google Cloud Storage) ---
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
    GS_FILE_OVERWRITE = False
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'
    # MEDIA_ROOT is not used for GCS

# --------------------------------------------------
# 🧾 DEFAULT PRIMARY KEY FIELD
# --------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------
# 🌐 GLOBAL CONTEXT PROCESSOR (for SYSTEM values)
# --------------------------------------------------
def system_context(request):
    """Inject SYSTEM settings globally in templates (e.g. {{ SYSTEM.SYSTEM_NAME }})"""
    return {'SYSTEM': SYSTEM}

# (The old 'if DEBUG:' print block at the end is no longer needed)
