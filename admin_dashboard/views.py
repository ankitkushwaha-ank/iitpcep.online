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


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.contrib import messages


# Import your models: Question, Option, etc.

@login_required(login_url='admin_dashboard:admin_login')
@user_passes_test(lambda u: u.is_superuser, login_url='admin_dashboard:admin_login')
def add_question(request):
    if request.method == "POST":
        parent_type = request.POST.get('parent_type')
        parent_id = request.POST.get('parent_id')

        # Get text arrays (Text inputs allow empty strings, so arrays work fine here)
        q_types = request.POST.getlist('question_type[]')
        q_texts = request.POST.getlist('question_text[]')

        # Option Text Arrays
        opt_texts = {
            'A': request.POST.getlist('opt_a_text[]'),
            'B': request.POST.getlist('opt_b_text[]'),
            'C': request.POST.getlist('opt_c_text[]'),
            'D': request.POST.getlist('opt_d_text[]'),
        }

        correct_answers_text = request.POST.getlist('correct_answer_text[]')

        try:
            with transaction.atomic():
                for i, q_type in enumerate(q_types):

                    # Get Text safely
                    text = q_texts[i] if i < len(q_texts) else ""

                    # FIX: Get Image using specific Key (question_image_0, question_image_1)
                    # This solves the issue of images shifting to the wrong question
                    q_img = request.FILES.get(f'question_image_{i}')

                    # Skip if completely empty (no text AND no image)
                    if not text.strip() and not q_img:
                        continue

                    question = Question.objects.create(
                        parent_type=parent_type,
                        parent_id=parent_id,
                        question_type=q_type,
                        text=text,
                        image=q_img,
                        marks=1
                    )

                    # Handle MCQ Options
                    if q_type == 'MCQ':
                        # Correct Option (e.g. correct_opt_0 = 'A')
                        correct_val = request.POST.get(f'correct_opt_{i}')
                        question.correct_option = correct_val
                        question.save()

                        # Create Options A, B, C, D
                        for label in ['A', 'B', 'C', 'D']:
                            # Get text from array
                            o_text_list = opt_texts[label]
                            o_text = o_text_list[i] if i < len(o_text_list) else ""

                            # Get Option Image from unique key (e.g. opt_a_img_0)
                            o_img = request.FILES.get(f'opt_{label.lower()}_img_{i}')

                            Option.objects.create(
                                question=question,
                                option_label=label,
                                text=o_text,
                                image=o_img
                            )

                    # Handle Text/Code
                    elif q_type in ['TEXT', 'CODE']:
                        ans_text = correct_answers_text[i] if i < len(correct_answers_text) else ''
                        question.correct_answer_text = ans_text
                        question.save()

            messages.success(request, "Questions added successfully.")

        except Exception as e:
            messages.error(request, f"Error adding questions: {str(e)}")

    return redirect('admin_dashboard:admin_dashboard')


@login_required(login_url='admin_dashboard:admin_login')
def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    if request.method == "POST":
        try:
            # 1. Update Question Text
            # We use [0] because the modal sends arrays even for single edits
            q_texts = request.POST.getlist('question_text[]')
            question.text = q_texts[0] if q_texts else question.text

            # 2. Update Question Image
            # Edit Modal resets counter to 0, so we look for 'question_image_0'
            if request.FILES.get('question_image_0'):
                question.image = request.FILES.get('question_image_0')

            question.save()

            # 3. Update Options (MCQ)
            if question.question_type == 'MCQ':

                # Update Correct Option
                correct_val = request.POST.get('correct_opt_0')
                if correct_val:
                    question.correct_option = correct_val
                    question.save()

                # Update A, B, C, D
                for label in ['A', 'B', 'C', 'D']:
                    # Get Inputs
                    txt_list = request.POST.getlist(f'opt_{label.lower()}_text[]')
                    new_text = txt_list[0] if txt_list else ""

                    new_img = request.FILES.get(f'opt_{label.lower()}_img_0')

                    # Use update_or_create to handle cases where options might be missing
                    obj, created = Option.objects.update_or_create(
                        question=question,
                        option_label=label,
                        defaults={'text': new_text}
                    )

                    # Only update image if a new one is uploaded
                    if new_img:
                        obj.image = new_img
                        obj.save()

            # 4. Update Text/Code Answer
            elif question.question_type in ['TEXT', 'CODE']:
                ans_list = request.POST.getlist('correct_answer_text[]')
                question.correct_answer_text = ans_list[0] if ans_list else ""
                question.save()

            messages.success(request, "Question updated successfully.")

        except Exception as e:
            messages.error(request, f"Error updating question: {str(e)}")

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