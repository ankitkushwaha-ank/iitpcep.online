from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.db import transaction

from .models import (
    SystemConfig, UserTable,
    Course, Assignment, Quiz, Exam,
    Question, Option, CalendarEvent
)

# ==================================================
# 🖊️ WIDGETS: CKEditor if available, else fallback
# ==================================================
try:
    # pip install django-ckeditor
    from ckeditor.widgets import CKEditorWidget  # type: ignore
    RichTextWidget = CKEditorWidget
except Exception:
    from django.forms.widgets import Textarea
    class RichTextWidget(Textarea):
        pass


# ==================================================
# ⚙️ SYSTEM CONFIGURATION (Editable)
# ==================================================
@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = (
        "status_badge",
        "system_status",
        "system_pin",
        "system_root",
        "last_updated",
    )
    list_display_links = ("status_badge",)
    list_editable = ("system_status", "system_pin", "system_root")
    readonly_fields = ("last_updated",)
    actions = ["activate_system", "shutdown_system", "reset_pin"]

    def status_badge(self, obj):
        color = "green" if obj.system_status == "ONLINE" else "red"
        return format_html(f"<b style='color:{color};'>{obj.system_status}</b>")
    status_badge.short_description = "Status"

    def activate_system(self, request, queryset):
        queryset.update(system_status="ONLINE", last_updated=timezone.now())
        self.message_user(request, "✅ System is now ONLINE", messages.SUCCESS)

    def shutdown_system(self, request, queryset):
        queryset.update(system_status="OFFLINE", last_updated=timezone.now())
        self.message_user(request, "⚠️ System has been SHUT DOWN", messages.WARNING)

    def reset_pin(self, request, queryset):
        queryset.update(system_pin="4321", last_updated=timezone.now())
        self.message_user(request, "🔑 System PIN reset to 4321", messages.INFO)


# ==================================================
# 👥 USER MANAGEMENT ADMIN (Editable)
# ==================================================
@admin.register(UserTable)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "is_admin",
        "is_banned",
        "status_badge",
        "is_online",
        "last_active",
        "created_at",
    )
    list_editable = ("is_admin", "is_banned", "is_online")
    search_fields = ("username",)
    list_filter = ("is_admin", "is_banned", "is_online")
    readonly_fields = ("last_active",)

    actions = ["promote_to_admin", "ban_users", "unban_users"]

    def status_badge(self, obj):
        if obj.is_banned:
            return format_html("<span style='color:red; font-weight:bold;'>BANNED</span>")
        elif obj.is_online:
            return format_html("<span style='color:green; font-weight:bold;'>🟢 Online</span>")
        elif obj.is_admin:
            return format_html("<span style='color:blue; font-weight:bold;'>ADMIN</span>")
        return format_html("<span style='color:gray;'>🔴 Offline</span>")
    status_badge.short_description = "Status"

    def promote_to_admin(self, request, queryset):
        count = queryset.update(is_admin=True)
        self.message_user(request, f"✅ {count} user(s) promoted to admin.", messages.SUCCESS)

    def ban_users(self, request, queryset):
        count = queryset.update(is_banned=True, is_online=False)
        self.message_user(request, f"⛔ {count} user(s) banned.", messages.WARNING)

    def unban_users(self, request, queryset):
        count = queryset.update(is_banned=False)
        self.message_user(request, f"✅ {count} user(s) unbanned.", messages.SUCCESS)

    promote_to_admin.short_description = "Promote to Admin"
    ban_users.short_description = "Ban Users"
    unban_users.short_description = "Unban Users"


# ==================================================
# 📘 COURSE ADMIN (Editable + Image Support)
# ==================================================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("image_preview", "code", "title", "description")
    search_fields = ("title", "code", "description")
    fields = ("title", "code", "description", "image", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:80px; height:60px; object-fit:cover; border-radius:6px;" />',
                obj.image.url,
            )
        return "No Image"
    image_preview.short_description = "Preview"


# ==================================================
# 🧩 RICH DESCRIPTION FOR ASSESSMENTS
# ==================================================
class AssessmentForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=RichTextWidget())
    class Meta:
        fields = "__all__"


# ==================================================
# 🧠 BULK QUESTIONS: Helper forms
# ==================================================
TEST_TYPE_CHOICES = (
    ("ASSIGNMENT", "Assignment"),
    ("QUIZ", "Quiz"),
    ("EXAM", "Exam"),
)

class QuestionBulkChooseForm(forms.Form):
    """Step 1 form: choose type, course, and specific test."""
    test_type = forms.ChoiceField(choices=TEST_TYPE_CHOICES)
    course = forms.ModelChoiceField(queryset=Course.objects.all())
    # test will be chosen after course + type submitted (in same form re-render)
    test = forms.ChoiceField(required=False)

class QuestionBulkPasteForm(forms.Form):
    """Step 2 form: paste many questions + options quickly."""
    payload = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 18, "style": "font-family:monospace;"}),
        help_text=(
            "Format example:\n"
            "Q: What is 2+2?\n"
            "A) 1\nB) 2\nC) 3\nD) 4 *\n\n"
            "Q: Short text type\n"
            "TEXT: Answer goes here\n"
            "(Use * to mark correct MCQ option; leave TEXT for open answer.)"
        )
    )


def _get_test_queryset(test_type, course):
    if test_type == "ASSIGNMENT":
        return Assignment.objects.filter(course=course)
    if test_type == "QUIZ":
        return Quiz.objects.filter(course=course)
    return Exam.objects.filter(course=course)


def _create_question_with_options(parent_type, parent_id, qtext, options, correct_label=None, allow_custom=False):
    q = Question.objects.create(
        parent_type=parent_type,
        parent_id=parent_id,
        question_type="MCQ" if options else "TEXT",
        marks=1,
        allow_custom_answer=allow_custom,
        text=qtext.strip(),
    )
    if options:
        for label, text in options:
            opt = Option.objects.create(
                question=q,
                option_label=label,
                text=text.strip(),
            )
            if correct_label and label == correct_label:
                q.correct_option = opt
                q.save(update_fields=["correct_option"])
    else:
        q.correct_answer_text = ""  # optional
        q.save()
    return q


def _parse_bulk_payload(payload):
    """
    Parse the textarea content into list of entries:
    Each entry becomes: { 'qtext': str, 'options': [(label, text),...], 'correct': 'B' or None, 'allow_custom': bool }
    """
    entries = []
    block = []
    lines = [ln.rstrip() for ln in payload.splitlines()]
    lines.append("")  # sentinel to flush

    def flush(block_lines):
        if not block_lines:
            return
        qtext = ""
        options = []
        correct = None
        allow_custom = False
        # build
        for ln in block_lines:
            if ln.startswith("Q:"):
                qtext = ln[2:].strip(": ").strip()
            elif ln.upper().startswith("TEXT:"):
                qtext = qtext or "(Short answer)"
                allow_custom = True
            elif len(ln) >= 3 and ln[1] == ")":  # like "A) something"
                label = ln[0].upper()
                text = ln[2:].strip()
                if text.endswith("*"):
                    text = text[:-1].rstrip()
                    correct = label
                options.append((label, text))
        entries.append({
            "qtext": qtext,
            "options": options,
            "correct": correct,
            "allow_custom": allow_custom and not options,
        })

    for ln in lines:
        if ln.strip() == "":
            flush(block)
            block = []
        else:
            block.append(ln)
    return entries


# ==================================================
# 📚 BASE ASSESSMENT ADMIN (Editable + Add Questions)
# ==================================================
class BaseAssessmentAdmin(admin.ModelAdmin):
    form = AssessmentForm

    list_display = (
        "title",
        "course",
        "open_date",
        "close_date",
        "max_attempts",
        "duration_minutes",
        "is_live",
        "status_label",
    )
    list_editable = (
        "open_date",
        "close_date",
        "max_attempts",
        "duration_minutes",
        "is_live",
    )
    list_filter = ("course", "is_live")
    search_fields = ("title", "description")
    ordering = ("-open_date",)
    actions = ["make_live", "stop_live"]

    # ----- status label
    def status_label(self, obj):
        color = "green" if obj.is_live else "red"
        text = "LIVE" if obj.is_live else "OFFLINE"
        return format_html(f"<b style='color:{color};'>{text}</b>")
    status_label.short_description = "Status"

    def make_live(self, request, queryset):
        count = queryset.update(is_live=True, updated_at=timezone.now())
        self.message_user(request, f"✅ {count} assessment(s) are now LIVE!", messages.SUCCESS)

    def stop_live(self, request, queryset):
        count = queryset.update(is_live=False, updated_at=timezone.now())
        self.message_user(request, f"🔒 {count} assessment(s) stopped.", messages.WARNING)

    # ----- object-tools: "Add questions"
    def get_urls(self):
        urls = super().get_urls()
        my = [
            path("<int:object_id>/questions/", self.admin_site.admin_view(self.add_questions_view),
                 name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_add_questions"),
        ]
        return my + urls

    def add_view(self, request, form_url="", extra_context=None):
        # After creating, you’ll see the object-tools “Add questions” on change page
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # Inject a link for “Add questions”
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            url = reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_add_questions",
                          args=[obj.pk])
            extra_context["add_questions_url"] = url
            extra_context["show_save"] = True
        return super().change_view(request, object_id, form_url, extra_context)

    @transaction.atomic
    def add_questions_view(self, request, object_id):
        """
        Bulk-add questions for this specific assessment instance.
        """
        obj = get_object_or_404(self.model, pk=object_id)
        parent_type = self.model.__name__.upper()  # ASSIGNMENT / QUIZ / EXAM
        parent_id = obj.pk

        if request.method == "POST":
            form = QuestionBulkPasteForm(request.POST)
            if form.is_valid():
                entries = _parse_bulk_payload(form.cleaned_data["payload"])
                created = 0
                for e in entries:
                    _create_question_with_options(
                        parent_type=parent_type,
                        parent_id=parent_id,
                        qtext=e["qtext"],
                        options=e["options"],
                        correct_label=e["correct"],
                        allow_custom=e["allow_custom"],
                    )
                    created += 1
                self.message_user(request, f"✅ {created} question(s) added.", messages.SUCCESS)
                return redirect(reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change", args=[object_id]))
        else:
            form = QuestionBulkPasteForm()

        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta,
            original=obj,
            title=f"Bulk add questions for {obj}",
            form=form,
        )
        return render(request, "admin/bulk_add_questions.html", context)


# Register assessment admins
@admin.register(Assignment)
class AssignmentAdmin(BaseAssessmentAdmin):
    pass

@admin.register(Quiz)
class QuizAdmin(BaseAssessmentAdmin):
    pass

@admin.register(Exam)
class ExamAdmin(BaseAssessmentAdmin):
    pass


# ==================================================
# ❓ QUESTION + OPTION MANAGEMENT (Editable)
# ==================================================
class OptionInline(admin.TabularInline):
    model = Option
    extra = 2
    fields = ("option_label", "text", "image")
    show_change_link = True

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_text",
        "parent_type",
        "parent_id",
        "question_type",
        "marks",
        "correct_option",
        "allow_custom_answer",
    )
    list_editable = ("marks", "allow_custom_answer", "correct_option")
    list_filter = ("parent_type", "question_type")
    search_fields = ("text",)
    inlines = [OptionInline]

    fieldsets = (
        ("Question Details", {
            "fields": ("parent_type", "parent_id", "question_type", "marks", "allow_custom_answer")
        }),
        ("Content", {
            "fields": ("text", "image", "correct_option", "correct_answer_text")
        }),
    )

    def short_text(self, obj):
        return (obj.text or "")[:60] + ("..." if obj.text and len(obj.text) > 60 else "")
    short_text.short_description = "Question"


# ==================================================
# 🗓️ CALENDAR EVENT ADMIN (Editable)
# ==================================================
@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ("title", "event_type", "related_course", "date")
    list_editable = ("event_type", "related_course", "date")
    list_filter = ("event_type",)
    search_fields = ("title", "description")
    ordering = ("-date",)


# ==================================================
# 🧠 ADMIN DASHBOARD HEADER + SUMMARY
# ==================================================
admin.site.site_header = "🏫 IITP College E-Portal"
admin.site.site_title = "IITPCEP Admin Panel"
admin.site.index_title = "📘 College Moodle Administration Dashboard"


def system_summary(modeladmin, request, queryset):
    total_users = UserTable.objects.count()
    online_users = UserTable.objects.filter(is_online=True).count()
    banned_users = UserTable.objects.filter(is_banned=True).count()
    admins = UserTable.objects.filter(is_admin=True).count()
    total_courses = Course.objects.count()
    total_assignments = Assignment.objects.count()
    total_quizzes = Quiz.objects.count()
    total_exams = Exam.objects.count()

    messages.info(
        request,
        f"📊 Users: {total_users} | 🟢 Online: {online_users} | 👑 Admins: {admins} | ⛔ Banned: {banned_users} | "
        f"📘 Courses: {total_courses} | 🧾 Assignments: {total_assignments} | 🧩 Quizzes: {total_quizzes} | 🧪 Exams: {total_exams}"
    )

class QuestionsWizardAdmin(ModelAdmin):
    change_list_template = "admin/questions_wizard.html"