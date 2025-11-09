import os

# Base project directory
base_dir = "iitpcep"

# Folder structure dictionary
structure = {
    base_dir: [
        "manage.py",
        "config.py",
        "requirements.txt",
        "db.sqlite3",
        {
            "iitpcep": [
                "__init__.py",
                "settings.py",
                "urls.py",
                "wsgi.py",
                "asgi.py",
            ]
        },
        {
            "moodle": [
                "__init__.py",
                "admin.py",
                "apps.py",
                "models.py",
                "views.py",
                "urls.py",
                "forms.py",
                {
                    "templates": [
                        "dashboard.html",
                        "login.html",
                        "courses.html",
                        "assignments.html",
                        "quiz.html",
                        "exams.html",
                        "calendar.html",
                    ]
                },
                {
                    "static": [
                        {"css": []},
                        {"js": []},
                        {"images": []},
                    ]
                },
            ]
        },
    ]
}


def create_structure(base_path, struct):
    """Recursively create directories and files."""
    for item in struct:
        if isinstance(item, dict):
            for folder, contents in item.items():
                folder_path = os.path.join(base_path, folder)
                os.makedirs(folder_path, exist_ok=True)
                create_structure(folder_path, contents)
        else:
            # Create file
            file_path = os.path.join(base_path, item)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("")  # create empty file


# ✅ Ensure the base directory exists first
os.makedirs(base_dir, exist_ok=True)

# ✅ Create the full structure
create_structure(".", [structure])
print(f"✅ Project structure created successfully under '{base_dir}/'!")

# --- Optional: Add boilerplate code ---
manage_py = f"""#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iitpcep.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
"""

urls_py = """from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('moodle.urls')),
]
"""

moodle_urls_py = """from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
"""

moodle_views_py = """from django.shortcuts import render, redirect
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        pin = request.POST.get('pin')
        if username == 'admin' and pin == '1234':
            request.session['username'] = username
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or PIN.')
    return render(request, 'login.html')

def dashboard(request):
    if not request.session.get('username'):
        return redirect('login')
    return render(request, 'dashboard.html', {'username': request.session['username']})
"""

# ✅ Write minimal boilerplate content
files_to_write = {
    os.path.join(base_dir, "manage.py"): manage_py,
    os.path.join(base_dir, "iitpcep", "urls.py"): urls_py,
    os.path.join(base_dir, "moodle", "urls.py"): moodle_urls_py,
    os.path.join(base_dir, "moodle", "views.py"): moodle_views_py,
}

for path, content in files_to_write.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("\n✅ Added base Django boilerplate files successfully!")
print("💡 Next: Activate venv, install Django, and run 'python manage.py runserver' inside 'iitpcep/' folder.")
