from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from config import SYSTEM
from django.views.decorators.csrf import csrf_exempt
from .models import (
    UserTable,
    SystemConfig,
    Course,
    Assignment,
    Quiz,
    Exam,
    Question,
    Option,
    CalendarEvent,
)


# --------------------------------------------------
# 🔐 LOGIN VIEW — Global PIN System
# --------------------------------------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        pin = request.POST.get('pin', '').strip()

        # ✅ Get system configuration
        system_config = SystemConfig.objects.first()
        system_pin = system_config.system_pin if system_config else SYSTEM.get("SYSTEM_PIN", "4321")
        system_status = system_config.system_status if system_config else "ONLINE"

        # 🔴 Block login if system is offline
        if system_status == "OFFLINE":
            messages.error(request, "🚫 System is currently offline. Try again later.")
            return render(request, "offline.html", {"system_status": "OFFLINE"})

        # ✅ Check PIN
        if pin == system_pin:
            # Create or get user
            user, created = UserTable.objects.get_or_create(username=username)

            # Save to session
            request.session['username'] = user.username
            user.is_online = True
            user.last_active = timezone.now()
            user.save(update_fields=["is_online", "last_active"])

            return redirect('dashboard')
        else:
            messages.error(request, "Incorrect PIN. Please try again.")

    return render(request, "login.html")


import calendar
from datetime import datetime
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    UserTable, SystemConfig, Assignment, Quiz, Exam, Course, CalendarEvent
)
from itertools import chain
from collections import defaultdict


# --------------------------------------------------
# 🏠 DASHBOARD VIEW (with CALENDAR & TIMELINE)
# --------------------------------------------------
def dashboard(request):
    # ✅ 1. GET SYSTEM CONFIG & AUTH
    config = SystemConfig.objects.first()
    pin_required = True if not config else getattr(config, "pin_required", True)
    username = request.session.get("username")

    # ✅ 2. HANDLE LOGIN & GUESTS
    if pin_required and not username:
        return redirect("login")
    if not username and not pin_required:
        username = "Guest"

    # ✅ 3. VALIDATE USER & ACTIVITY
    user = UserTable.objects.filter(username=username).first()
    if user:
        if user.is_banned:
            messages.error(request, "🚫 Your account is banned.")
            request.session.flush()
            return redirect("login")
        user.is_online = True
        user.last_active = timezone.now()
        user.save(update_fields=["is_online", "last_active"])

    # ✅ 4. HANDLE SYSTEM OFFLINE
    if config and config.system_status == "OFFLINE":
        return render(request, "offline.html", {"system_status": config.system_status})

    now = timezone.now()
    courses = Course.objects.all()

    # --------------------------------------------------
    # 🗓️ 5. LIVE ASSESSMENTS (for main dashboard cards)
    # --------------------------------------------------
    live_now_filter = Q(
        is_live=True,
        open_date__lte=now
    ) & (
                              Q(close_date__gte=now) | Q(close_date__isnull=True)
                      )
    live_assignments = Assignment.objects.filter(live_now_filter)
    live_quizzes = Quiz.objects.filter(live_now_filter)
    live_exams = Exam.objects.filter(live_now_filter)

    # --------------------------------------------------
    # 🗓️ 6. TIMELINE LOGIC
    # --------------------------------------------------

    # ✅ UPDATE: Removed 'Q(is_live=True)' so it shows drafts/offline tests too
    timeline_filter = (
            Q(close_date__gte=now) | Q(close_date__isnull=True)
    )

    all_activities = sorted(
        list(chain(
            Assignment.objects.filter(timeline_filter).select_related('course'),
            Quiz.objects.filter(timeline_filter).select_related('course'),
            Exam.objects.filter(timeline_filter).select_related('course')
        )),
        # Sort by close date, put "Open Indefinitely" (None) at the very end
        key=lambda x: x.close_date or datetime(9999, 1, 1, tzinfo=timezone.utc)
    )

    # --- Pre-process the data for the template ---
    timeline_events = []
    for activity in all_activities:
        date_group = "Open Indefinitely"
        if activity.close_date:
            date_group = activity.close_date.date()

        timeline_events.append({
            "id": activity.id,
            "title": activity.title,
            "course": activity.course,
            "close_date": activity.close_date,
            "model_name": activity.__class__.__name__,
            "model_name_lower": activity.__class__.__name__.lower(),
            "close_date_group": date_group,
            "is_live": activity.is_live,  # ✅ Added this so you can show a 'Draft' badge in HTML
        })

    # --------------------------------------------------
    # 🗓️ 7. CALENDAR LOGIC (Updated for Modal Data)
    # --------------------------------------------------
    try:
        year = int(request.GET.get('year', now.year))
        month = int(request.GET.get('month', now.month))
    except ValueError:
        year = now.year
        month = now.month

    current_date = datetime(year, month, 1)
    today = timezone.now().date()
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    calendar_matrix = cal.monthdayscalendar(year, month)

    first_day_of_month = current_date.replace(day=1)
    last_day_prev_month = first_day_of_month - timezone.timedelta(days=1)
    first_day_next_month = (first_day_of_month + timezone.timedelta(days=32)).replace(day=1)

    prev_month_data = {
        "year": last_day_prev_month.year,
        "month_num": last_day_prev_month.month,
        "month_name": last_day_prev_month.strftime('%B')
    }
    next_month_data = {
        "year": first_day_next_month.year,
        "month_num": first_day_next_month.month,
        "month_name": first_day_next_month.strftime('%B')
    }

    month_filter = Q(open_date__year=year, open_date__month=month) | \
                   Q(close_date__year=year, close_date__month=month)

    cal_assignments = Assignment.objects.filter(month_filter).select_related('course')
    cal_quizzes = Quiz.objects.filter(month_filter).select_related('course')
    cal_exams = Exam.objects.filter(month_filter).select_related('course')
    other_events = CalendarEvent.objects.filter(date__year=year, date__month=month)

    events_by_day = {}

    def add_to_dict(day, event_data):
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event_data)

    # --- UPDATED LOOP: PASSING FULL DATA FOR MODAL ---
    for item in list(cal_assignments) + list(cal_quizzes) + list(cal_exams):
        model_name = item.__class__.__name__  # e.g. "Quiz"

        # 1. Handle "Opens" Date
        if item.open_date.month == month:
            add_to_dict(item.open_date.day, {
                "id": item.id,
                "title": item.title,
                "type": "opens",
                "model": model_name,
                "model_name_lower": model_name.lower(),  # Required for {% url %}
                "start_date": item.open_date,  # Required for date format
                "course": item.course,  # Required for Course Code/Title
                "is_active": True  # Logic to show/hide button
            })

        # 2. Handle "Closes" Date
        if item.close_date and item.close_date.month == month:
            add_to_dict(item.close_date.day, {
                "id": item.id,
                "title": item.title,
                "type": "closes",
                "model": model_name,
                "model_name_lower": model_name.lower(),
                "start_date": item.close_date,
                "course": item.course,
                "is_active": True
            })

    # --- UPDATED OTHER EVENTS ---
    for event in other_events:
        add_to_dict(event.date.day, {
            "id": event.id,
            "title": event.title,
            "type": event.get_event_type_display(),  # e.g. "Course Event"
            "model": "calendarevent",
            "model_name_lower": "calendarevent",
            "start_date": event.date,
            "course": None,  # CalendarEvents might not have courses
            "is_active": False
        })

    # --- PROCESS WEEKS (Mostly the same) ---
    calendar_weeks_with_events = []
    for week in calendar_matrix:
        processed_week = []
        day_index = 0
        for day_num in week:
            if day_num == 0:
                processed_week.append({"day_num": 0, "events": [], "classes": "dayblank"})
            else:
                day_events = events_by_day.get(day_num, [])

                # Sort events by time if possible
                day_events.sort(key=lambda x: x['start_date'])

                day_classes = ["day", "text-sm-center", "text-md-left", "clickable"]

                # Check Today
                if day_num == today.day and month == today.month and year == today.year:
                    day_classes.append("today")

                # Check Events
                if day_events:
                    day_classes.append("hasevent")

                # Check Weekend (Sat=5, Sun=6)
                if day_index >= 5:
                    day_classes.append("weekend")

                processed_week.append({
                    "day_num": day_num,
                    "events": day_events,
                    "classes": " ".join(day_classes)
                })
            day_index += 1
        calendar_weeks_with_events.append(processed_week)
    # --------------------------------------------------
    # 8. COMBINE ALL CONTEXT & RENDER
    # --------------------------------------------------
    context = {
        "username": username,
        "assignments": live_assignments,
        "quizzes": live_quizzes,
        "exams": live_exams,
        "system_status": config.system_status if config else "ONLINE",
        "pin_required": pin_required,
        "courses": courses,
        "calendar_weeks": calendar_weeks_with_events,
        "current_month_name": current_date.strftime('%B'),
        "current_year": year,
        "current_month_num": month,
        "prev_month": prev_month_data,
        "next_month": next_month_data,
        "today": today,

        # Pass the correctly named list
        "timeline_activities": timeline_events,
    }

    return render(request, "dashboard.html", context)

# --------------------------------------------------
# 🧩 ASSESSMENT VIEW (Assignment, Quiz, Exam)
# --------------------------------------------------
def assessment_view(request, parent_type, parent_id):
    model_map = {
        "ASSIGNMENT": Assignment,
        "QUIZ": Quiz,
        "EXAM": Exam,
    }

    model_class = model_map.get(parent_type.upper())
    if not model_class:
        messages.error(request, "Invalid assessment type.")
        return redirect("dashboard")

    parent = get_object_or_404(model_class, id=parent_id)

    # 🚫 Restrict access if not live
    if not parent.is_live:
        messages.warning(request, f"⚠️ This {parent_type.lower()} is not live right now.")
        return redirect("dashboard")

    # Fetch all questions linked to this assessment
    questions = Question.objects.filter(
        parent_type=parent_type.upper(),
        parent_id=parent.id
    ).prefetch_related("options")

    return render(request, "assessment_view.html", {
        "assessment": parent,
        "questions": questions,
        "type": parent_type.upper(),
        "username": request.session.get("username"),
    })


# --------------------------------------------------
# 🧾 ASSIGNMENT VIEW
# --------------------------------------------------
def assignment_view(request, assignment_id):
    return assessment_view(request, "ASSIGNMENT", assignment_id)


# --------------------------------------------------
# 🧩 QUIZ VIEW
# --------------------------------------------------
def quiz_view(request, quiz_id):
    return assessment_view(request, "QUIZ", quiz_id)


# --------------------------------------------------
# 🧪 EXAM VIEW
# --------------------------------------------------
def exam_view(request, exam_id):
    return assessment_view(request, "EXAM", exam_id)


# --------------------------------------------------
# 🗓️ CALENDAR VIEW
# --------------------------------------------------
def calendar_view(request):
    username = request.session.get("username")
    if not username:
        return redirect("login")

    events = CalendarEvent.objects.all().order_by('-date')
    return render(request, "calendar.html", {
        "events": events,
        "username": username,
    })

def mycourses_view(request):
    # Fetch all courses (you can later filter by user enrollment)
    courses = Course.objects.all().order_by("code")

    # Pass to template context
    context = {
        "courses": courses,
    }

    return render(request, "mycourses.html", context)

def course_detail_view(request, course_code):
    course = get_object_or_404(Course, code=course_code)

    assignments = Assignment.objects.filter(course=course).order_by("open_date")
    quizzes = Quiz.objects.filter(course=course).order_by("open_date")
    exams = Exam.objects.filter(course=course).order_by("open_date")

    return render(request, "course_page.html", {
        "course": course,
        "assignments": assignments,
        "quizzes": quizzes,
        "exams": exams,
    })

def test_detail_view(request, test_type, test_id):
    test_type = test_type.upper()
    model_map = {
        "ASSIGNMENT": Assignment,
        "QUIZ": Quiz,
        "EXAM": Exam,
    }

    if test_type not in model_map:
        return render(request, "404.html", {"message": "Invalid test type."})

    model = model_map[test_type]
    test_obj = get_object_or_404(model, id=test_id)

    # ✅ Prefetch related options correctly
    questions = Question.objects.filter(
        parent_type=test_type,
        parent_id=test_id
    ).prefetch_related("options")  # change to "option_set" if no related_name exists
    courses = Course.objects.all()
    quiz_end = False
    if test_obj.close_date and timezone.now() > test_obj.close_date:
        quiz_end = True
    context = {
        "test": test_obj,
        "questions": questions,
        "test_type": test_type.capitalize(),
        "page_title": f"{test_type.capitalize()}: {test_obj.title}",
        "courses":courses,
        "quiz_end": quiz_end,
    }

    return render(request, "quiz.html", context)


from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Assignment, Quiz, Exam, Question, Option


def test_attempt_view(request, test_type, test_id):
    """
    Displays paginated attempt page (1 question per page)
    with course details, navigation, correct answer preselection,
    and text-answer support.
    """
    test_type = test_type.capitalize()

    # ✅ Map model type
    model_map = {
        "Assignment": Assignment,
        "Quiz": Quiz,
        "Exam": Exam,
    }

    if test_type not in model_map:
        return render(request, "404.html", {"message": "Invalid test type."})

    model = model_map[test_type]
    test_obj = get_object_or_404(model, id=test_id)

    # ✅ Fetch related course (if it exists)
    course_obj = getattr(test_obj, "course", None)

    course_name = "Unknown Course"
    if course_obj:
        # If your Course model has attributes like 'code' and 'name'
        code = getattr(course_obj, "code", "") or getattr(course_obj, "course_code", "")
        name = getattr(course_obj, "name", "") or getattr(course_obj, "title", "")
        if code and name:
            course_name = f"{code}: {name}"
        elif name:
            course_name = name
        elif code:
            course_name = code

    # ✅ Fetch all questions
    questions = list(
        Question.objects.filter(parent_type__iexact=test_type, parent_id=test_id)
        .prefetch_related("options")
        .order_by("id")
    )
    total = len(questions)

    if not questions:
        return render(request, "attempt.html", {
            "test": test_obj,
            "test_type": test_type,
            "questions_list": [],
            "error": "No questions found for this test.",
        })

    # ✅ Determine current question index
    try:
        q_index = int(request.GET.get("q", 1)) - 1
    except ValueError:
        q_index = 0
    q_index = max(0, min(q_index, total - 1))

    question = questions[q_index]
    options = list(question.options.all())

    # ✅ Initialize session for answers
    if "user_answers" not in request.session:
        request.session["user_answers"] = {}
    user_answers = request.session["user_answers"]

    # ✅ Handle submission
    if request.method == "POST":
        selected = request.POST.get(str(question.id))
        flagged = request.POST.get(f"q{question.id}_flagged") == "1"

        # Save in session
        user_answers[str(question.id)] = {
            "answer": selected,
            "flagged": flagged,
        }
        request.session["user_answers"] = user_answers
        request.session.modified = True

        # Navigation
        if "next" in request.POST and q_index + 1 < total:
            return redirect(f"{reverse('test_attempt', args=[test_type.lower(), test_id])}?q={q_index + 2}")
        elif "previous" in request.POST and q_index > 0:
            return redirect(f"{reverse('test_attempt', args=[test_type.lower(), test_id])}?q={q_index}")
        elif "finish" in request.POST:
            return render(request, "attempt_finish.html", {
                "test": test_obj,
                "test_type": test_type,
                "user_answers": user_answers,
                "course_name": course_name,
            })

    # ✅ Restore saved answer
    saved_data = user_answers.get(str(question.id), {})
    question.user_answer = saved_data.get("answer", "")
    question.flagged = saved_data.get("flagged", False)

    # ✅ Correct Answer Logic
    correct_option_id = None
    correct_answer_text = None

    # For text-based answers
    if question.correct_answer_text:
        correct_answer_text = question.correct_answer_text.strip()

    # For MCQs: match by option_label (A, B, C, D)
    if question.correct_option:
        correct_label = question.correct_option.strip().upper()
        correct_option = next(
            (opt for opt in options if opt.option_label.strip().upper() == correct_label),
            None
        )
        if correct_option:
            correct_option_id = str(correct_option.id)

    # ✅ Annotate options
    for opt in options:
        opt.is_correct = (str(opt.id) == str(correct_option_id))
        opt.is_selected = (str(opt.id) == str(question.user_answer))

    courses = Course.objects.all()
    config = SystemConfig.objects.first()
    show_answer_value = config.show_answer

    # ✅ Context for template
    context = {
        "test": test_obj,
        "test_type": test_type,
        "course_name": course_name,
        "question": question,
        "options": options,
        "total": total,
        "q_index": q_index + 1,
        "page_title": f"{test_obj.title} (page {q_index + 1} of {total})",
        "questions_list": questions,
        "correct_option": correct_option_id,
        "correct_text": correct_answer_text,
        "courses":courses,
        "show_answer":show_answer_value,
    }

    return render(request, "attempt.html", context)


from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from .models import Assignment, Quiz, Exam, Question, Course

def test_finish_view(request, test_type, test_id):
    """
    Displays the finish summary page with all questions and their statuses.
    Fetches data consistent with test_attempt_view.
    """
    test_type = test_type.capitalize()

    # ✅ Map model type
    model_map = {
        "Assignment": Assignment,
        "Quiz": Quiz,
        "Exam": Exam,
    }

    if test_type not in model_map:
        return render(request, "404.html", {"message": "Invalid test type."})

    model = model_map[test_type]
    test_obj = get_object_or_404(model, id=test_id)

    # ✅ Fetch course details (if available)
    course_obj = getattr(test_obj, "course", None)
    course_name = "Unknown Course"
    if course_obj:
        code = getattr(course_obj, "code", "") or getattr(course_obj, "course_code", "")
        name = getattr(course_obj, "name", "") or getattr(course_obj, "title", "")
        if code and name:
            course_name = f"{code}: {name}"
        elif name:
            course_name = name
        elif code:
            course_name = code

    # ✅ Fetch all questions (same query as test_attempt_view)
    questions = list(
        Question.objects.filter(parent_type__iexact=test_type, parent_id=test_id)
        .prefetch_related("options")
        .order_by("id")
    )

    # ✅ Get user answers from session
    user_answers = request.session.get("user_answers", {})

    # ✅ Build question summary list
    questions_summary = []
    for idx, q in enumerate(questions, start=1):
        user_data = user_answers.get(str(q.id), {})
        is_answered = bool(user_data.get("answer"))
        is_flagged = user_data.get("flagged", False)
        questions_summary.append({
            "index": idx,
            "id": q.id,
            "status": "Answer saved" if is_answered else "Not yet answered",
            "answered": is_answered,
            "flagged": is_flagged,
        })


    config = SystemConfig.objects.first()
    show_answer_value = config.show_answer

    context = {
        "test": test_obj,
        "test_type": test_type,
        "course_name": course_name,
        "questions_list": questions_summary,  # ✅ same variable name your template expects
        "total": len(questions),
        "show_answer":show_answer_value,
    }

    return render(request, "finish.html", context)


from django.shortcuts import render, get_object_or_404
from .models import Assignment, Quiz, Exam, Question

def test_review_view(request, test_type, test_id):
    """
    Displays a review page showing all questions, user answers, and correct answers.
    """
    test_type = test_type.capitalize()

    # ✅ Map model type
    model_map = {
        "Assignment": Assignment,
        "Quiz": Quiz,
        "Exam": Exam,
    }

    if test_type not in model_map:
        return render(request, "404.html", {"message": "Invalid test type."})

    model = model_map[test_type]
    test_obj = get_object_or_404(model, id=test_id)

    # ✅ Fetch all questions for the test
    questions = list(
        Question.objects.filter(parent_type__iexact=test_type, parent_id=test_id)
        .prefetch_related("options")
        .order_by("id")
    )

    # Debugging: Check if questions are being fetched
    if not questions:
        print(f"No questions found for test: {test_type} with ID: {test_id}")

    # ✅ Get saved answers from session
    user_answers = request.session.get("user_answers", {})

    # Initialize user_answers if not present
    if not user_answers:
        user_answers = {}

    # ✅ Prepare question data with user answers and correct answers
    question_data = []
    for q in questions:
        # Get the user answer
        user_answer = user_answers.get(str(q.id), {}).get("answer")

        # Prepare the question options and correct answer
        options = list(q.options.all())
        correct_option_id = None
        correct_answer_text = None

        if q.correct_answer_text:
            correct_answer_text = q.correct_answer_text.strip()

        if q.correct_option:
            correct_option = next(
                (opt for opt in options if opt.option_label.strip().upper() == q.correct_option.strip().upper()),
                None
            )
            if correct_option:
                correct_option_id = correct_option.id

        # Add the data to the list
        question_data.append({
            "id": q.id,
            "text": q.text,
            "image": q.image if hasattr(q, "image") else None,
            "options": options,
            "correct_option": correct_option_id,
            "correct_answer_text": correct_answer_text,
        })

    config = SystemConfig.objects.first()
    show_answer_value = config.show_answer

    context = {
        "test": test_obj,
        "test_type": test_type,
        "questions": question_data,
        "user_answers": user_answers,
        "total_questions": len(questions),
        "show_answer":show_answer_value,
    }

    # Render the review page
    return render(request, "review.html", context)



# --------------------------------------------------
# 🚪 LOGOUT VIEW
# --------------------------------------------------
def logout_view(request):
    username = request.session.get("username")
    if username:
        UserTable.objects.filter(username=username).update(is_online=False)
    request.session.flush()
    return redirect("dashboard")
