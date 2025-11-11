import os
from pathlib import Path
from config import DATABASE, SYSTEM  # ✅ import DB + system config safely
import os
import json
import pymysql
from google.oauth2 import service_account
from cloud_sql_python_connector import connector

# --- Load Google Credentials from Environment ---
# This is the core of the production setup. It loads the JSON string
# from the environment variable and creates a single 'credentials' object.

credentials = None
GS_CREDENTIALS = None  # for django-storages

# 1. Get the JSON string from the environment
GOOGLE_CREDENTIALS_JSON_STR = os.environ.get('GOOGLE_CREDENTIALS_JSON')

if GOOGLE_CREDENTIALS_JSON_STR:
    try:
        # 2. Parse the JSON string into a dictionary
        info = json.loads(GOOGLE_CREDENTIALS_JSON_STR)

        # 3. Create the credentials object
        credentials = service_account.Credentials.from_service_account_info(info)

        # 4. Pass the same credentials to django-storages
        GS_CREDENTIALS = credentials
    except Exception as e:
        print(f"Error loading Google credentials from JSON: {e}")
else:
    print("WARNING: 'GOOGLE_CREDENTIALS_JSON' environment variable not set.")

# --- Cloud SQL (MySQL) Production Configuration ---

# This is a required fix for the connector to work with PyMySQL
pymysql.version_info = (1, 4, 6)
pymysql.install_as_MySQLdb()

# 1. Initialize the Cloud SQL Connector *with our credentials*
# This one 'credentials' object handles auth for both DB and Storage
db_connector = connector.Connector(credentials=credentials)


# 2. This function is called by Django to get a database connection
def get_db_conn():
    conn = db_connector.connect(
        os.environ.get('DB_HOST', ''),  # 'project:region:instance'
        "pymysql",
        user=os.environ.get('DB_USER', ''),
        password=os.environ.get('DB_PASS', ''),
        db=os.environ.get('DB_NAME', ''),
    )
    return conn


# 3. Configure Django's DATABASES setting
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        # We use 'CONN_CALLABLE' to tell Django to use our connector function
        # The other fields are ignored, but NAME is still needed.
        'CONN_CALLABLE': get_db_conn,
    }
}

# --- Google Cloud Storage (GCS) Production Configuration ---

# We already set GS_CREDENTIALS at the top.
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
GS_FILE_OVERWRITE = False

# The URLs will be built using your bucket name
MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'

# --------------------------------------------------
# 📁 BASE CONFIG
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key')

# ⚙️ Debug & Allowed Hosts
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1','iitpcep.online', 'www.iitpcep.online', 'https://iitpcep-online.onrender.com','iitpcep-online.onrender.com','cet.iitpcep.online']
CSRF_TRUSTED_ORIGINS = [
    'https://iitpcep.online',
    'https://www.iitpcep.online',
    'https://iitpcep-online.onrender.com',
    'cet.iitpcep.online'
]

# Redirect Django login checks to your custom admin login
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
    'moodle',
    "admin_dashboard",
]
INSTALLED_APPS += ["ckeditor"]


# --------------------------------------------------
# ⚙️ MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'moodle.middleware.SystemStatusMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
                # ✅ Custom system config available globally
                'iitpcep.settings.system_context',
                'moodle.context_processors.global_user_context',
            ],
        },
    },
]




# --------------------------------------------------
# 📦 STATIC & MEDIA FILES
# --------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'moodle', 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # ✅ Used in production for collectstatic
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # ✅ Optional but recommended


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


# --------------------------------------------------
# ✅ DEV MODE DEBUG LOG
# --------------------------------------------------
if DEBUG:
    print("--------------------------------------------------")
    print(f"[SETTINGS] Environment: {'Development' if DEBUG else 'Production'}")
    print(f"[SETTINGS] Using Database Engine: {DATABASES['default']['ENGINE']}")
    print(f"[SETTINGS] System Online: {SYSTEM.get('SYSTEM_ON', True)}")
    print(f"[SETTINGS] Base Directory: {BASE_DIR}")
    print("--------------------------------------------------")
