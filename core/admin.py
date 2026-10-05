import logging
from django.contrib import admin
from .models import Venue, Speaker, Session, Registration, UnansweredQuestion
from core.reindex import run_reindex

logger = logging.getLogger(__name__)


def trigger_reindex(modeladmin, request, queryset):
    """
    Admin action: rebuilds the RAG index directly, in-process.

    No external service involved - this used to relay through an n8n
    webhook (Django -> n8n -> Django), but that round trip added an
    external dependency without adding any real capability: n8n wasn't
    doing any branching, scheduling, or multi-service orchestration here,
    just bouncing the call back to the same app. Calling run_reindex()
    directly is simpler, has one less thing that can fail, and needs no
    n8n account at all for this particular task.

    (n8n is still a good fit for Day 6's unanswered-question notification
    workflow, where it genuinely does something Django doesn't have built
    in - routing an alert to Slack/email.)
    """
    result = run_reindex()

    if result.get("status") == "ok":
        modeladmin.message_user(
            request, f"RAG index rebuilt successfully in {result['seconds']}s."
        )
    else:
        logger.warning("Reindex failed: %s", result.get("message"))
        modeladmin.message_user(
            request, f"Reindex failed: {result.get('message')}", level="ERROR"
        )


trigger_reindex.short_description = "Rebuild RAG index now"


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "building", "capacity")
    actions = [trigger_reindex]


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "email")
    search_fields = ("name",)
    actions = [trigger_reindex]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("title", "session_type", "venue", "start_time", "end_time", "track")
    list_filter = ("session_type", "track", "venue")
    search_fields = ("title",)
    filter_horizontal = ("speakers",)
    actions = [trigger_reindex]


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("student_name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("student_name", "email")


@admin.register(UnansweredQuestion)
class UnansweredQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "created_at")
    ordering = ("-created_at",)
    search_fields = ("question_text",)
    # Read-only: this is a log for organizers to review, not something
    # meant to be hand-edited through the admin form.
    readonly_fields = ("question_text", "created_at")

    def has_add_permission(self, request):
        return False
