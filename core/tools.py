"""
tools.py

The agent's toolbox. Each function here becomes one "tool" the LLM can choose
to call in Day 3's function-calling loop. Kept deliberately dumb and direct —
plain Django ORM queries, no LLM involved. This is the layer that guarantees
factual answers (schedule/venue/registration) instead of letting the model
guess or hallucinate.

Every function returns plain JSON-serializable data (dicts/lists), never
model instances directly, so it can be dropped straight into an LLM API's
tool_result content without extra work.

Design note: these are intentionally separate from rag/search.py. Anything
answerable from these structured tables should go through here, not RAG —
see the Day 1 discussion on the RAG/DB boundary.
"""

from datetime import datetime
from django.utils import timezone
from django.utils.dateparse import parse_date
from core.models import Session, Speaker, Venue, Registration


def get_schedule(date: str = None, track: str = None, speaker_name: str = None):
    """
    Look up sessions, optionally filtered by date, track, or speaker.

    Args:
        date: ISO date string, e.g. "2026-09-18". If omitted, returns all sessions.
        track: e.g. "AI/ML", "Data Engineering". Case-insensitive partial match.
        speaker_name: filter to sessions featuring a speaker whose name contains this.

    Returns:
        list of dicts, one per matching session, ordered by start time.
    """
    qs = Session.objects.all()

    if date:
        parsed = parse_date(date)
        if parsed is None:
            return {"error": f"Could not parse date '{date}'. Use YYYY-MM-DD."}
        qs = qs.filter(start_time__date=parsed)

    if track:
        qs = qs.filter(track__icontains=track)

    if speaker_name:
        qs = qs.filter(speakers__name__icontains=speaker_name)

    qs = qs.distinct().select_related("venue").prefetch_related("speakers")

    return [_serialize_session(s) for s in qs]


def get_speaker(name: str):
    """
    Look up a speaker by name (partial match) and their sessions.

    Args:
        name: full or partial speaker name, e.g. "Sharma" or "Dr. Ananya Sharma".

    Returns:
        dict with speaker info + their sessions, or an error dict if no match
        or if the name is ambiguous (matches multiple speakers).
    """
    matches = Speaker.objects.filter(name__icontains=name)
    count = matches.count()

    if count == 0:
        # Fall back to token matching: "Dr. Sharma" isn't a contiguous
        # substring of "Dr. Ananya Sharma", but every word in the query
        # ("dr", "sharma") does appear somewhere in that name. This covers
        # the common case of a title + surname without the middle name,
        # without pulling in a full fuzzy-matching library for it.
        tokens = [t.strip(".,") for t in name.split() if t.strip(".,")]
        candidates = Speaker.objects.all()
        for token in tokens:
            candidates = candidates.filter(name__icontains=token)
        matches = candidates
        count = matches.count()

    if count == 0:
        return {"error": f"No speaker found matching '{name}'."}
    if count > 1:
        return {
            "error": f"Multiple speakers match '{name}'.",
            "candidates": [s.name for s in matches],
        }

    speaker = matches.first()
    sessions = speaker.sessions.all().select_related("venue")

    return {
        "name": speaker.name,
        "title": speaker.title,
        "short_bio": speaker.short_bio,
        "sessions": [_serialize_session(s) for s in sessions],
    }


def get_venue(name: str = None):
    """
    Look up venue details, or list all venues if no name given.

    Args:
        name: venue name, partial match, e.g. "Auditorium". Omit to list all.

    Returns:
        dict with venue details (if name given and matched), or a list of
        all venues (if name omitted), or an error dict if no match.
    """
    if name is None:
        return [_serialize_venue(v) for v in Venue.objects.all()]

    matches = Venue.objects.filter(name__icontains=name)
    if not matches.exists():
        return {"error": f"No venue found matching '{name}'."}

    return _serialize_venue(matches.first())


def get_registration_status(email: str):
    """
    Look up a student's registration status by email.

    Args:
        email: the student's registered email address (exact match).

    Returns:
        dict with registration status and registered sessions, or an error
        dict if no registration is found for that email.
    """
    try:
        reg = Registration.objects.get(email__iexact=email)
    except Registration.DoesNotExist:
        return {"error": f"No registration found for '{email}'."}

    return {
        "student_name": reg.student_name,
        "email": reg.email,
        "status": reg.status,
        "registered_sessions": [
            _serialize_session(s) for s in reg.registered_sessions.all()
        ],
    }


# --- serialization helpers (keep model details out of the tool responses) ---

def _serialize_session(session: Session):
    return {
        "id": session.id,
        "title": session.title,
        "type": session.session_type,
        "track": session.track,
        "start_time": timezone.localtime(session.start_time).isoformat(),
        "end_time": timezone.localtime(session.end_time).isoformat(),
        "venue": session.venue.name if session.venue else None,
        "speakers": [sp.name for sp in session.speakers.all()],
        "description": session.description,
    }


def _serialize_venue(venue: Venue):
    return {
        "name": venue.name,
        "building": venue.building,
        "floor": venue.floor,
        "capacity": venue.capacity,
        "notes": venue.notes,
    }
