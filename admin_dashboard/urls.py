from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),

    # Courses
    path('course/add/', views.add_course, name='add_course'),
    path('course/edit/<int:course_id>/', views.edit_course, name='edit_course'),
    path('course/delete/<int:course_id>/', views.delete_course, name='delete_course'),

    # Assessments (Quiz, Assignment, Exam)
    path('assessment/add/', views.add_assessment, name='add_assessment'),

    # ✅ ADD THIS LINE BELOW TO FIX THE 404
    path('assessment/edit/<int:id>/', views.edit_assessment, name='edit_assessment'),

    path('assessment/delete/<int:id>/', views.delete_assessment, name='delete_assessment'),

    # Questions
    path('question/add/', views.add_question, name='add_question'),
    path('question/delete/<int:id>/', views.delete_question, name='delete_question'),

    # Users & Settings
    path('user/edit/', views.edit_user, name='edit_user'),
    path('user/ban/<int:user_id>/', views.toggle_ban_user, name='toggle_ban_user'),
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('settings/update/', views.update_settings, name='update_settings'),
]