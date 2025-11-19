from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.contrib.auth.models import User  # Standard Django User model
from datetime import datetime

# Auth Imports
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm

# Import your models
from moodle.models import (
    UserTable, SystemConfig, Course,
    Assignment, Quiz, Exam,
    Question, Option
)


# ---------------------------------------------------------
# 0. AUTHENTICATION & HELPERS
# ---------------------------------------------------------

def is_superuser(user):
    return user.is_authenticated and user.is_superuser


def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard:admin_dashboard')
        else:
            messages.error(request, "Access Denied: You are not an admin.")
            return redirect('/')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('admin_dashboard:admin_dashboard')
            else:
                messages.error(request, "Access Denied: Admin privileges required.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'admin_dashboard/login.html')


def admin_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('admin_dashboard:admin_login')


def _combine_date_time(date_str, time_str):
    if date_str and time_str:
        try:
            dt_str = f"{date_str} {time_str}"
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
        except ValueError:
            return None
    return None

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.core.serializers.json import DjangoJSONEncoder
import json
from datetime import datetime

# Import your models
from moodle.models import (
    UserTable, SystemConfig, Course,
    Assignment, Quiz, Exam,
    Question, Option, CalendarEvent
)

# ... (Keep Auth helpers like is_superuser, admin_login, etc. same as before) ...

# ---------------------------------------------------------
# 1. MAIN DASHBOARD VIEW (UPDATED WITH GRAPHS)
# ---------------------------------------------------------

@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def admin_dashboard(request):
    # --- 1. Standard Statistics ---
    total_users = UserTable.objects.count()
    online_users = UserTable.objects.filter(is_online=True).count()
    total_courses = Course.objects.count()
    total_quizzes = Quiz.objects.count()
    total_assignments = Assignment.objects.count()
    total_exams = Exam.objects.count()
    total_questions = Question.objects.count()

    # --- 2. Graph Data: User Growth (Line Chart) ---
    # Group users by creation month
    monthly_users = UserTable.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    user_labels = []
    user_data = []

    for entry in monthly_users:
        if entry['month']:
            user_labels.append(entry['month'].strftime('%b %Y'))
            user_data.append(entry['count'])

    # Fallback if no data
    if not user_data:
        user_labels = ["Jan", "Feb", "Mar", "Apr", "May"]
        user_data = [0, 0, 0, 0, 0]

    # --- 3. Graph Data: Content Distribution (Doughnut/Pie Chart) ---
    # Comparing count of Quizzes vs Assignments vs Exams
    distribution_labels = ["Quizzes", "Assignments", "Exams"]
    distribution_data = [total_quizzes, total_assignments, total_exams]

    # --- 4. Fetch Lists for Tables ---
    users = UserTable.objects.all().order_by('-created_at')
    courses = Course.objects.all()
    quizzes = Quiz.objects.all().order_by('-open_date')
    assignments = Assignment.objects.all().order_by('-open_date')
    exams = Exam.objects.all().order_by('-open_date')
    questions = Question.objects.all().order_by('-id')

    # --- 5. System Config ---
    system_config, created = SystemConfig.objects.get_or_create(id=1)

    context = {
        'stats': {
            'total_users': total_users,
            'online_users': online_users,
            'total_courses': total_courses,
            'total_quizzes': total_quizzes,
            'total_assignments': total_assignments,
            'total_exams': total_exams,
            'total_questions': total_questions,
        },
        # Pass JSON strings for Chart.js
        'graphs': {
            'user_labels': json.dumps(user_labels),
            'user_data': json.dumps(user_data),
            'dist_labels': json.dumps(distribution_labels),
            'dist_data': json.dumps(distribution_data),
        },
        'users': users,
        'courses': courses,
        'quizzes': quizzes,
        'assignments': assignments,
        'exams': exams,
        'questions': questions,
        'config': system_config,
    }
    return render(request, 'admin_dashboard/admin.html', context)

@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def add_course(request):
    if request.method == "POST":
        try:
            Course.objects.create(
                title=request.POST.get('title'),
                code=request.POST.get('code'),
                description=request.POST.get('description'),
                image=request.FILES.get('image')
            )
            messages.success(request, "Course added successfully!")
        except IntegrityError:
            messages.error(request, "Error: Course Code must be unique.")
    return redirect('admin_dashboard:admin_dashboard')


@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        course.title = request.POST.get('title')
        course.code = request.POST.get('code')
        course.description = request.POST.get('description')
        if request.FILES.get('image'):
            course.image = request.FILES.get('image')
        course.save()
        messages.success(request, "Course updated successfully.")
    return redirect('admin_dashboard:admin_dashboard')


@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    messages.success(request, "Course deleted.")
    return redirect('admin_dashboard:admin_dashboard')


# ---------------------------------------------------------
# 3. ASSESSMENT MANAGEMENT
# ---------------------------------------------------------

@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def add_assessment(request):
    if request.method == "POST":
        assess_type = request.POST.get('assessment_type')
        course_id = request.POST.get('course_id')

        data = {
            'course': get_object_or_404(Course, id=course_id),
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'duration_minutes': request.POST.get('duration_minutes'),
            'max_attempts': request.POST.get('max_attempts', 1),
            'is_live': request.POST.get('is_live') == 'on',
            'open_date': _combine_date_time(request.POST.get('open_date'), request.POST.get('open_time')),
            'close_date': _combine_date_time(request.POST.get('close_date'), request.POST.get('close_time'))
        }

        if assess_type == 'quiz':
            Quiz.objects.create(**data)
        elif assess_type == 'assignment':
            Assignment.objects.create(**data)
        elif assess_type == 'exam':
            Exam.objects.create(**data)

        messages.success(request, f"{assess_type.capitalize()} created successfully!")
    return redirect('admin_dashboard:admin_dashboard')


@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def edit_assessment(request, type, id):
    # Logic to handle editing would typically involve fetching the object based on type
    # This requires a separate page or a modal that submits to a specific URL
    # For simplicity in this single-page app, we redirect back.
    # Implement specific update logic here if needed.
    return redirect('admin_dashboard:admin_dashboard')


@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def delete_assessment(request, id):
    # Try to find and delete in order
    if Quiz.objects.filter(id=id).exists():
        Quiz.objects.get(id=id).delete()
    elif Assignment.objects.filter(id=id).exists():
        Assignment.objects.get(id=id).delete()
    elif Exam.objects.filter(id=id).exists():
        Exam.objects.get(id=id).delete()

    messages.success(request, "Assessment deleted.")
    return redirect('admin_dashboard:admin_dashboard')


# ---------------------------------------------------------
# 4. QUESTION BANK MANAGEMENT (FIXED: OPTIONS SAVING)
# ---------------------------------------------------------

@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def add_question(request):
    if request.method == "POST":
        parent_type = request.POST.get('parent_type')
        parent_id = request.POST.get('parent_id')

        # Arrays from HTML
        q_types = request.POST.getlist('question_type[]')
        q_texts = request.POST.getlist('question_text[]')
        q_images = request.FILES.getlist('question_image[]')

        # Option Arrays (Text)
        opt_a_texts = request.POST.getlist('opt_a_text[]')
        opt_b_texts = request.POST.getlist('opt_b_text[]')
        opt_c_texts = request.POST.getlist('opt_c_text[]')
        opt_d_texts = request.POST.getlist('opt_d_text[]')

        # Option Arrays (Images) - *Note: File list indexing matches creation order in HTML*
        opt_a_imgs = request.FILES.getlist('opt_a_img[]')
        opt_b_imgs = request.FILES.getlist('opt_b_img[]')
        opt_c_imgs = request.FILES.getlist('opt_c_img[]')
        opt_d_imgs = request.FILES.getlist('opt_d_img[]')

        correct_answers_text = request.POST.getlist('correct_answer_text[]')

        try:
            with transaction.atomic():
                for i, text in enumerate(q_texts):
                    if not text: continue

                    # 1. Create Question
                    q_img = q_images[i] if i < len(q_images) else None

                    question = Question.objects.create(
                        parent_type=parent_type,
                        parent_id=parent_id,
                        question_type=q_types[i],
                        text=text,
                        image=q_img,
                        marks=1
                    )

                    # 2. Handle Options if MCQ
                    if q_types[i] == 'MCQ':
                        # Get Correct Option Value (Radio button name is dynamic: correct_opt_0, correct_opt_1...)
                        correct_val = request.POST.get(f'correct_opt_{i}')
                        question.correct_option = correct_val
                        question.save()

                        # Create 4 Options
                        # Helper to get image safely
                        def get_opt_img(img_list, idx):
                            return img_list[idx] if idx < len(img_list) else None

                        Option.objects.create(question=question, option_label='A', text=opt_a_texts[i],
                                              image=get_opt_img(opt_a_imgs, i))
                        Option.objects.create(question=question, option_label='B', text=opt_b_texts[i],
                                              image=get_opt_img(opt_b_imgs, i))
                        Option.objects.create(question=question, option_label='C', text=opt_c_texts[i],
                                              image=get_opt_img(opt_c_imgs, i))
                        Option.objects.create(question=question, option_label='D', text=opt_d_texts[i],
                                              image=get_opt_img(opt_d_imgs, i))

                    # 3. Handle Text/Code Answer
                    elif q_types[i] in ['TEXT', 'CODE']:
                        question.correct_answer_text = correct_answers_text[i]
                        question.save()

            messages.success(request, "Questions and options added successfully.")

        except Exception as e:
            messages.error(request, f"Error adding questions: {str(e)}")

    return redirect('admin_dashboard:admin_dashboard')


@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def delete_question(request, id):
    q = get_object_or_404(Question, id=id)
    q.delete()
    messages.success(request, "Question deleted.")
    return redirect('admin_dashboard:admin_dashboard')


# ---------------------------------------------------------
# 5. USER & SETTINGS
# ---------------------------------------------------------

@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def edit_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        # Logic to update user based on username or ID passed
        # For security, usually ID is safer
        messages.success(request, "User updated.")
    return redirect('admin_dashboard:admin_dashboard')


@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def toggle_ban_user(request, user_id):
    user = get_object_or_404(UserTable, id=user_id)
    user.is_banned = not user.is_banned
    user.save()
    messages.info(request, f"User status updated.")
    return redirect('admin_dashboard:admin_dashboard')


@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def delete_user(request, user_id):
    user = get_object_or_404(UserTable, id=user_id)
    user.delete()
    messages.warning(request, "User deleted.")
    return redirect('admin_dashboard:admin_dashboard')


@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def update_settings(request):
    if request.method == "POST":
        config, _ = SystemConfig.objects.get_or_create(id=1)
        config.system_status = "ONLINE" if request.POST.get('system_status_toggle') == 'on' else "OFFLINE"
        config.system_pin = request.POST.get('system_pin')
        config.pin_required = request.POST.get('pin_required') == 'Yes'
        config.save()
        messages.success(request, "Settings updated.")
    return redirect('admin_dashboard:admin_dashboard')


# ... imports ...

# ---------------------------------------------------------
# 3. ASSESSMENT MANAGEMENT (Add & Edit)
# ---------------------------------------------------------

@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(is_superuser, login_url='admin_dashboard:admin_login')
def edit_assessment(request, id):
    """
    Handles updating a Quiz, Assignment, or Exam.
    """
    if request.method == "POST":
        assess_type = request.POST.get('assessment_type')  # 'quiz', 'assignment', or 'exam'

        # 1. Determine which model to edit
        obj = None
        if assess_type == 'quiz':
            obj = get_object_or_404(Quiz, id=id)
        elif assess_type == 'assignment':
            obj = get_object_or_404(Assignment, id=id)
        elif assess_type == 'exam':
            obj = get_object_or_404(Exam, id=id)

        if obj:
            # 2. Update Fields
            obj.title = request.POST.get('title')
            obj.description = request.POST.get('description')

            # Update Course relationship
            course_id = request.POST.get('course_id')
            obj.course = get_object_or_404(Course, id=course_id)

            # Update Dates/Time
            obj.open_date = _combine_date_time(request.POST.get('open_date'), request.POST.get('open_time'))
            obj.close_date = _combine_date_time(request.POST.get('close_date'), request.POST.get('close_time'))

            # Update Settings
            obj.duration_minutes = request.POST.get('duration_minutes')
            obj.max_attempts = request.POST.get('max_attempts', 1)
            obj.is_live = request.POST.get('is_live') == 'on'

            obj.save()
            messages.success(request, f"{assess_type.capitalize()} updated successfully!")

    return redirect('admin_dashboard:admin_dashboard')