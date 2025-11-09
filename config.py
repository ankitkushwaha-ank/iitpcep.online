import os
from pathlib import Path

# --------------------------------------------------
# 📁 BASE DIRECTORY
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

# --------------------------------------------------
# 🌐 ENVIRONMENT DETECTION
# --------------------------------------------------
DJANGO_ENV = os.getenv("DJANGO_ENV", "development").lower()

# --------------------------------------------------
# ⚙️ DEFAULT SYSTEM SETTINGS
# --------------------------------------------------
SYSTEM = {
    "SYSTEM_NAME": "IITP College E-Portal",
    "SYSTEM_URL": "https://iitpcep.online",
    "SYSTEM_PIN": "4321",
    "SYSTEM_ON": True,
}

# --------------------------------------------------
# 🧠 DATABASE CONFIGURATION
# --------------------------------------------------
if DJANGO_ENV == "production":
    DATABASE = {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_NAME", "iitpcep"),
        "USER": os.getenv("MYSQL_USER", "iitpcep_user"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", "StrongPass@123"),
        "HOST": os.getenv("MYSQL_HOST", "185.199.52.85"),
        "PORT": os.getenv("MYSQL_PORT", "3306"),
        "OPTIONS": {"init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
    }
else:
    DATABASE = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

# --------------------------------------------------
# 👥 USER ROLES
# --------------------------------------------------
ROLES = {"ADMIN_USERS": ["admin", "system"]}

# --------------------------------------------------
# 🚀 FEATURE TOGGLES
# --------------------------------------------------
FEATURES = {
    "ALLOW_ASSIGNMENT_UPLOAD": True,
    "ALLOW_EXAM_VIEW": True,
    "ALLOW_CALENDAR_SYNC": True,
    "SHOW_ADMIN_DASHBOARD": True,
    "ALLOW_COURSE_CREATION": True,
}

# --------------------------------------------------
# ⚙️ SAFE HELPERS (no DB access here)
# --------------------------------------------------
def get_system_pin() -> str:
    return SYSTEM.get("SYSTEM_PIN", "4321")


def is_system_online() -> bool:
    return SYSTEM.get("SYSTEM_ON", True)


def is_admin_user(username: str) -> bool:
    return username.lower() in [u.lower() for u in ROLES["ADMIN_USERS"]]


def current_database_engine() -> str:
    return "MySQL (Production)" if "mysql" in DATABASE["ENGINE"] else "SQLite (Development)"

# --------------------------------------------------
# 🧾 DEBUG LOG (simple print only)
# --------------------------------------------------
print("--------------------------------------------------")
print(f"[CONFIG] Environment: {DJANGO_ENV.upper()}")
print(f"[CONFIG] Database Engine: {current_database_engine()}")
print(f"[CONFIG] System Online: {is_system_online()}")
print(f"[CONFIG] Global PIN: {get_system_pin()}")
print("--------------------------------------------------")
