from django.db import models


class Venue(models.Model):
    """Physical room/hall within the symposium venue."""
    name = models.CharField(max_length=200)           # e.g. "Auditorium A"
    building = models.CharField(max_length=200, blank=True)
    floor = models.CharField(max_length=50, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)               # e.g. "wheelchair accessible"

    def __str__(self):
        return self.name


class Speaker(models.Model):
    """A symposium speaker. Bio is short/structured here;
    longer bio text lives in the RAG documents, not here."""
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, blank=True)   # e.g. "Professor, IISc"
    short_bio = models.CharField(max_length=300, blank=True)
    photo_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


class Session(models.Model):
    """A scheduled talk/workshop. This is the core 'schedule' entity
    the agent's get_schedule / get_speaker tools query."""

    SESSION_TYPES = [
        ("talk", "Talk"),
        ("workshop", "Workshop"),
        ("panel", "Panel Discussion"),
        ("keynote", "Keynote"),
    ]

    title = models.CharField(max_length=300)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default="talk")
    speakers = models.ManyToManyField(Speaker, related_name="sessions")
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, related_name="sessions")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.TextField(blank=True)
    track = models.CharField(max_length=100, blank=True)   # e.g. "AI/ML", "Data Engineering"
    capacity = models.PositiveIntegerField(default=0)      # 0 = use venue capacity

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.title} ({self.start_time:%b %d, %H:%M})"


class Registration(models.Model):
    """A student's registration for the symposium and, optionally,
    specific sessions (for capacity-limited workshops)."""

    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("waitlisted", "Waitlisted"),
        ("cancelled", "Cancelled"),
    ]

    student_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")
    registered_sessions = models.ManyToManyField(Session, blank=True, related_name="registrations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} ({self.status})"


class UnansweredQuestion(models.Model):
    """
    Logs a question the agent couldn't match to any tool (the fallback
    case in the routing logic). Organizers can check these in Django
    admin to see what students are asking that the assistant can't
    currently handle - a gap-finding tool, not a chat feature.
    """
    question_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.question_text[:60]
