from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from moodle.models import (
    UserTable, Course, Assignment, Quiz, Exam,
    Question, Option, SystemConfig, CalendarEvent
)




def offline_view(request):
    """Show an offline or restricted access page."""
    return render(request, "admin_dashboard/offline.html")


# =========================================================
# 🏠 DASHBOARD
# =========================================================

def dashboard(request):
    context = {
        "total_users": UserTable.objects.count(),
        "online_users": UserTable.objects.filter(is_online=True).count(),
        "banned_users": UserTable.objects.filter(is_banned=True).count(),
        "admins": UserTable.objects.filter(is_admin=True).count(),
        "total_courses": Course.objects.count(),
        "assignments": Assignment.objects.count(),
        "quizzes": Quiz.objects.count(),
        "exams": Exam.objects.count(),
        "events": CalendarEvent.objects.order_by("-date")[:5],
        "system": SystemConfig.objects.first(),
    }
    return render(request, "admin_dashboard/dashboard.html", context)


# =========================================================
# 👥 USER MANAGEMENT
# =========================================================

def users_view(request):
    users = UserTable.objects.all().order_by("-created_at")

    # Promote / Ban / Unban directly via POST
    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("user_id")
        user = get_object_or_404(UserTable, id=user_id)

        if action == "promote":
            user.is_admin = True
            user.save()
            messages.success(request, f"👑 {user.username} promoted to Admin.")
        elif action == "ban":
            user.is_banned = True
            user.is_online = False
            user.save()
            messages.warning(request, f"🚫 {user.username} has been banned.")
        elif action == "unban":
            user.is_banned = False
            user.save()
            messages.success(request, f"✅ {user.username} unbanned.")
        elif action == "delete":
            user.delete()
            messages.info(request, "🗑️ User deleted successfully.")
        return redirect("admin_users")

    return render(request, "admin_dashboard/users.html", {"users": users})


# =========================================================
# 📘 COURSES
# =========================================================

def courses_view(request):
    courses = Course.objects.all().order_by("title")

    if request.method == "POST":
        title = request.POST.get("title")
        code = request.POST.get("code")
        desc = request.POST.get("description")
        img = request.FILES.get("image")

        Course.objects.create(title=title, code=code, description=desc, image=img)
        messages.success(request, f"📚 Course '{title}' added successfully.")
        return redirect("admin_courses")

    return render(request, "admin_dashboard/courses.html", {"courses": courses})



def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    messages.info(request, f"🗑️ Course '{course.title}' deleted.")
    return redirect("admin_courses")


# =========================================================
# 🧩 TESTS: Assignments / Quizzes / Exams
# =========================================================

def tests_view(request):
    assignments = Assignment.objects.all()
    quizzes = Quiz.objects.all()
    exams = Exam.objects.all()
    return render(request, "admin_dashboard/tests.html", {
        "assignments": assignments,
        "quizzes": quizzes,
        "exams": exams,
    })


# ---------- CRUD for each type ----------

def add_assignment(request):
    if request.method == "POST":
        course_id = request.POST.get("course")
        title = request.POST.get("title")
        desc = request.POST.get("description")
        course = get_object_or_404(Course, id=course_id)
        Assignment.objects.create(course=course, title=title, description=desc)
        messages.success(request, f"🧾 Assignment '{title}' added.")
        return redirect("admin_tests")

    return render(request, "admin_dashboard/assignments.html", {"assignments": Assignment.objects.all()})



def add_quiz(request):
    if request.method == "POST":
        course_id = request.POST.get("course")
        title = request.POST.get("title")
        desc = request.POST.get("description")
        course = get_object_or_404(Course, id=course_id)
        Quiz.objects.create(course=course, title=title, description=desc)
        messages.success(request, f"🧩 Quiz '{title}' added.")
        return redirect("admin_tests")

    return render(request, "admin_dashboard/queizs.html", {"quizzes": Quiz.objects.all()})



def add_exam(request):
    if request.method == "POST":
        course_id = request.POST.get("course")
        title = request.POST.get("title")
        desc = request.POST.get("description")
        course = get_object_or_404(Course, id=course_id)
        Exam.objects.create(course=course, title=title, description=desc)
        messages.success(request, f"🧪 Exam '{title}' added.")
        return redirect("admin_tests")

    return render(request, "admin_dashboard/exams.html", {"exams": Exam.objects.all()})


# =========================================================
# ❓ QUESTIONS & OPTIONS
# =========================================================

def questions_view(request):
    questions = Question.objects.all().select_related().order_by("-id")

    if request.method == "POST":
        parent_type = request.POST.get("parent_type")
        parent_id = request.POST.get("parent_id")
        qtext = request.POST.get("text")
        qtype = request.POST.get("question_type")
        marks = request.POST.get("marks") or 1
        correct_option = request.POST.get("correct_option")
        allow_custom = bool(request.POST.get("allow_custom"))
        img = request.FILES.get("image")

        q = Question.objects.create(
            parent_type=parent_type,
            parent_id=parent_id,
            question_type=qtype,
            text=qtext,
            marks=marks,
            correct_option=correct_option,
            allow_custom_answer=allow_custom,
            image=img,
        )

        # Add options for MCQs
        if qtype == "MCQ":
            for label in ["A", "B", "C", "D"]:
                text = request.POST.get(f"option_{label}")
                if text:
                    Option.objects.create(question=q, option_label=label, text=text)

        messages.success(request, f"✅ Question added successfully.")
        return redirect("admin_questions")

    return render(request, "admin_dashboard/questions.html", {"questions": questions})



def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    question.delete()
    messages.info(request, "🗑️ Question deleted.")
    return redirect("admin_questions")


# =========================================================
# ⚙️ SYSTEM CONFIGURATION
# =========================================================

def system_config_view(request):
    config = SystemConfig.objects.first()
    if request.method == "POST":
        config.system_status = request.POST.get("status")
        config.system_pin = request.POST.get("pin")
        config.pin_required = "pin_required" in request.POST
        config.last_updated = timezone.now()
        config.save()
        messages.success(request, "✅ System configuration updated successfully.")
        return redirect("admin_system")

    return render(request, "admin_dashboard/system.html", {"config": config})


# =========================================================
# 🗓️ CALENDAR EVENTS
# =========================================================

def events_view(request):
    events = CalendarEvent.objects.all().order_by("-date")

    if request.method == "POST":
        title = request.POST.get("title")
        date = request.POST.get("date")
        desc = request.POST.get("description")
        event_type = request.POST.get("event_type")
        related_course_id = request.POST.get("related_course")

        related_course = Course.objects.filter(id=related_course_id).first() if related_course_id else None

        CalendarEvent.objects.create(
            title=title,
            date=date,
            description=desc,
            event_type=event_type,
            related_course=related_course,
        )
        messages.success(request, f"📅 Event '{title}' created successfully.")
        return redirect("admin_events")

    return render(request, "admin_dashboard/events.html", {
        "events": events,
        "courses": Course.objects.all()
    })



def delete_event(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id)
    event.delete()
    messages.info(request, "🗑️ Event deleted.")
    return redirect("admin_events")

# =========================================================
# 🔐 Django Admin Username/Password Login
# =========================================================
from django.contrib.auth import authenticate, login, logout

def admin_login_view(request):
    """Login using Django's built-in admin username and password."""
    if request.user.is_authenticated:
        return redirect("admin_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff or user.is_superuser:  # ✅ only allow admin users
                login(request, user)
                messages.success(request, f"✅ Welcome back, {user.username}!")
                return redirect("admin_dashboard")
            else:
                messages.error(request, "🚫 Access denied. Admin privileges required.")
        else:
            messages.error(request, "❌ Invalid username or password.")

    return render(request, "admin_dashboard/login.html")


def admin_logout_view(request):
    """Logout the admin user."""
    logout(request)
    messages.info(request, "👋 You’ve been logged out.")
    return redirect("admin_login")
