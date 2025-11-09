from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 🏠 DASHBOARD
    # ==========================================
    path("", views.dashboard, name="admin_dashboard"),

    # ==========================================
    # 👥 USERS
    # ==========================================
    path("users/", views.users_view, name="admin_users"),
    path("offline/", views.offline_view, name="admin_offline"),

    # ==========================================
    # 📘 COURSES
    # ==========================================
    path("courses/", views.courses_view, name="admin_courses"),
    path("courses/delete/<int:course_id>/", views.delete_course, name="admin_delete_course"),

    # ==========================================
    # 🧩 TESTS (Assignments / Quizzes / Exams)
    # ==========================================
    path("tests/", views.tests_view, name="admin_tests"),

    # Assignment CRUD
    path("tests/assignments/add/", views.add_assignment, name="admin_add_assignment"),

    # Quiz CRUD
    path("tests/quizzes/add/", views.add_quiz, name="admin_add_quiz"),

    # Exam CRUD
    path("tests/exams/add/", views.add_exam, name="admin_add_exam"),

    # ==========================================
    # ❓ QUESTIONS
    # ==========================================
    path("questions/", views.questions_view, name="admin_questions"),
    path("questions/delete/<int:question_id>/", views.delete_question, name="admin_delete_question"),

    # ==========================================
    # ⚙️ SYSTEM CONFIGURATION
    # ==========================================
    path("system/", views.system_config_view, name="admin_system"),

    # ==========================================
    # 🗓️ CALENDAR EVENTS
    # ==========================================
    path("events/", views.events_view, name="admin_events"),
    path("events/delete/<int:event_id>/", views.delete_event, name="admin_delete_event"),

    # ==========================================
    # 🔐 PIN LOGIN (Optional)
    # ==========================================
    path("login/", views.admin_login_view, name="admin_login"),
    path("logout/", views.admin_logout_view, name="admin_logout"),
]
