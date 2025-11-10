import os
from pathlib import Path
from config import DATABASE, SYSTEM  # ✅ import DB + system config safely

# --------------------------------------------------
# 📁 BASE CONFIG
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key')

# ⚙️ Debug & Allowed Hosts
DEBUG = False
ALLOWED_HOSTS = ['iitpcep.online', 'www.iitpcep.online', 'https://iitpcep-online.onrender.com','iitpcep-online.onrender.com','cet.iitpcep.online']

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
# 🧠 DATABASE CONFIGURATION (safe fallback)
# --------------------------------------------------
from config import DATABASE

DATABASES = {}
try:
    if DATABASE and isinstance(DATABASE, dict) and DATABASE.get("ENGINE"):
        DATABASES["default"] = DATABASE
    else:
        raise ValueError("Invalid DATABASE object in config.py")
except Exception as e:
    print(f"[SETTINGS WARNING] Database config failed ({e}) — using SQLite fallback.")
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }



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
