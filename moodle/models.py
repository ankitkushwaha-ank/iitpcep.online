from django.db import models
from django.utils import timezone
from datetime import timedelta


# --------------------------------------------------
# 🧑 USER MODEL (PIN-BASED LOGIN SYSTEM)
# --------------------------------------------------


class UserTable(models.Model):
    username = models.CharField(max_length=100, unique=True)
    is_admin = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ New Fields for Online Tracking
    last_active = models.DateTimeField(default=timezone.now, help_text="Last time the user was active.")
    is_online = models.BooleanField(default=False, help_text="Whether the user is currently online or not.")

    def __str__(self):
        return self.username

    # ✅ Automatically determine online/offline state
    def update_activity(self):
        """Call this whenever user does something (like visiting a page)."""
        self.last_active = timezone.now()
        self.is_online = True
        self.save(update_fields=["last_active", "is_online"])

    def mark_offline(self):
        """Mark user offline manually or after timeout."""
        self.is_online = False
        self.save(update_fields=["is_online"])

    def is_recently_active(self):
        """Return True if user was active in last 5 minutes."""
        return timezone.now() - self.last_active <= timedelta(minutes=5)

    def status_label(self):
        """Used in admin panel or frontend."""
        if self.is_online or self.is_recently_active():
            return "🟢 Online"
        return "🔴 Offline"

    status_label.short_description = "Status"



# --------------------------------------------------
# ⚙️ SYSTEM CONFIGURATION MODEL
# --------------------------------------------------
class SystemConfig(models.Model):
    system_status = models.CharField(
        max_length=20,
        choices=[("ONLINE", "Online"), ("OFFLINE", "Offline")],
        default="ONLINE",
    )
    system_pin = models.CharField(max_length=10, default="4321")  # global PIN
    system_root = models.CharField(max_length=100, default="admin")
    pin_required = models.BooleanField(default=True, help_text="If disabled, PIN not required for login.")
    show_answer = models.BooleanField(default=True, help_text="If disabled, Answers not shows in Tests")
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SystemConfig ({self.system_status})"


# --------------------------------------------------
# 📘 COURSE MODEL
# --------------------------------------------------
class Course(models.Model):
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.FileField(upload_to="course_images/", blank=True, null=True)

    def __str__(self):
        return f"{self.code} - {self.title}"

# --------------------------------------------------
# 🧾 BASE MODEL (COMMON FOR ASSIGNMENT / QUIZ / EXAM)
# --------------------------------------------------
class BaseAssessment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    open_date = models.DateTimeField(default=timezone.now)
    close_date = models.DateTimeField(blank=True, null=True)

    duration_minutes = models.IntegerField(default=60, help_text="Total duration in minutes.")
    max_attempts = models.IntegerField(default=1, help_text="How many times a student can attempt.")

    # ✅ Admin-controlled Live toggle
    is_live = models.BooleanField(
        default=False,
        help_text="If enabled, this assessment becomes visible and attemptable by users."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def is_available(self):
        """
        Returns True if within open/close time AND is_live = True
        """
        now = timezone.now()
        return (
            self.is_live
            and self.open_date <= now
            and (self.close_date is None or now <= self.close_date)
        )

    def status_label(self):
        """Readable status for admin panel"""
        if not self.is_live:
            return "🔒 Not Live"
        elif not self.is_available():
            return "⏳ Scheduled"
        return "🟢 Live Now"

    status_label.short_description = "Status"


# --------------------------------------------------
# 📚 ASSIGNMENT / QUIZ / EXAM MODELS
# --------------------------------------------------
class Assignment(BaseAssessment):
    def __str__(self):
        return f"Assignment: {self.title}"


class Quiz(BaseAssessment):
    def __str__(self):
        return f"Quiz: {self.title}"


class Exam(BaseAssessment):
    def __str__(self):
        return f"Exam: {self.title}"


# --------------------------------------------------
# ❓ QUESTION MODEL (For MCQ, Coding, Image)
# --------------------------------------------------
class Question(models.Model):
    QUESTION_TYPES = [
        ("MCQ", "Multiple Choice Question"),
        ("CODE", "Coding Question"),
        ("TEXT", "Text Answer Question"),
    ]

    parent_type = models.CharField(
        max_length=20,
        choices=[("ASSIGNMENT", "Assignment"), ("QUIZ", "Quiz"), ("EXAM", "Exam")],
        default="QUIZ"
    )
    parent_id = models.PositiveIntegerField(help_text="ID of the parent Assignment/Quiz/Exam.")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default="MCQ")

    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="questions/", blank=True, null=True)

    marks = models.FloatField(default=1)
    allow_custom_answer = models.BooleanField(default=False, help_text="If enabled, user can type their own answer.")

    # ✅ Store correct answer
    correct_answer_text = models.TextField(blank=True, null=True, help_text="For text/coding questions.")
    correct_option = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
        help_text="Correct option label for MCQ."
    )

    def __str__(self):
        return f"Q{self.id}: {self.text[:40]}..." if self.text else f"Question {self.id}"


# --------------------------------------------------
# 🧩 OPTIONS (For MCQ QUESTIONS)
# --------------------------------------------------
class Option(models.Model):
    question = models.ForeignKey(Question, related_name="options", on_delete=models.CASCADE)
    option_label = models.CharField(
        max_length=1,
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]
    )
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="options/", blank=True, null=True)

    def __str__(self):
        return f"{self.option_label}: {self.text[:30] if self.text else 'Image Option'}"

    class Meta:
        ordering = ["option_label"]


# --------------------------------------------------
# 🗓️ CALENDAR EVENTS (System Announcements)
# --------------------------------------------------
class CalendarEvent(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True, null=True)

    related_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(
        max_length=50,
        choices=[
            ("ASSIGNMENT_OPEN", "Assignment Opened"),
            ("QUIZ_OPEN", "Quiz Opened"),
            ("EXAM_OPEN", "Exam Opened"),
            ("DEADLINE", "Submission Deadline"),
            ("NOTICE", "General Notice")
        ],
        default="NOTICE"
    )

    def __str__(self):
        return f"{self.title} ({self.event_type})"
