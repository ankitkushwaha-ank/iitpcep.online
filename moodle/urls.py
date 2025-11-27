from django.urls import path, include
from . import views

urlpatterns = [
    # =========================================
    # 🔐 AUTHENTICATION ROUTES
    # =========================================
    path('moodle/login.php', views.login_view, name='login'),
    path('moodle/logout', views.logout_view, name='logout'),

    # =========================================
    # 🏠 DASHBOARD + COURSES
    # =========================================
    path('', views.dashboard, name='home'),
    path('admincp/', include('admin_dashboard.urls')),
    path('moodle/my/admincp/', include('admin_dashboard.urls')),
    path('moodle/', views.dashboard, name='dashboard'),
    path('moodle/my/', views.dashboard, name='dashboard'),
    path('moodle/my/courses.php', views.mycourses_view, name='mycourses'),
    path('moodle/course/view.php?id=<int:course_code>', views.course_detail_view, name='course_detail'),

    # =========================================
    # 🧠 ASSESSMENTS (Assignments, Quizzes, Exams)
    # =========================================

    # -- Direct detail pages (info / instructions)
    path('moodle/mod/<str:test_type>/view.php?id=<int:test_id>', views.test_detail_view, name='test_detail'),

    # -- Attempt entry (handles single-question view)
    path("moodle/mod/<str:test_type>/cmid=<int:test_id>/attempt.php", views.test_attempt_view, name="test_attempt"),
    path("moodle/mod/<str:test_type>/cmid=<int:test_id>/finish.php&attempt=1", views.test_finish_view, name="test_finish"),
    path('moodle/mod/<str:test_type>/cmid=<int:test_id>/review.php&attempt=1', views.test_review_view, name='test_review'),


    # =========================================
    # 📅 CALENDAR / EVENTS / REMINDERS
    # =========================================
    path('calendar/', views.calendar_view, name='calendar_view'),

    # =========================================
    # ⚙️ FUTURE MODULES (Reports, Analytics, etc.)
    # =========================================
    # path('reports/', views.report_view, name='report_view'),
    # path('notifications/', views.notifications_view, name='notifications_view'),
]
