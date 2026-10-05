import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from core.tools import get_schedule, get_speaker, get_venue, get_registration_status
from core.models import UnansweredQuestion
from rag.search import search_documents


def index(request):
    """Renders the chat page."""
    return render(request, "chatui/index.html")


@csrf_exempt  # fine for a demo; in production use Django's CSRF token in the JS fetch instead
@require_POST
def api_chat(request):
    """
    Day 2 version: keyword routing picks a tool, the tool hits real data,
    and we format the result into a plain-language reply.

    This is NOT the real agent yet - the routing is still simple keyword
    matching, not LLM reasoning. Day 3 replaces _route_and_answer() with an
    actual LLM tool-calling loop (core/agent.py), where the MODEL decides
    which tool(s) to call, possibly chaining several. The response shape
    ({"reply": str, "tool_used": str|None}) stays the same, so the frontend
    doesn't change at all when that swap happens.
    """
    try:
        body = json.loads(request.body)
        message = body.get("message", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid request body"}, status=400)

    if not message:
        return JsonResponse({"error": "Message cannot be empty"}, status=400)

    reply, tool_used = _route_and_answer(message)
    return JsonResponse({"reply": reply, "tool_used": tool_used})


def _route_and_answer(message: str):
    """
    Rough keyword routing to a real tool, standing in for the LLM's
    tool-selection reasoning until Day 3's real agent replaces this.

    Order matters here: schedule/venue/registration keywords are checked
    first because "who is speaking tomorrow" should hit the schedule, not
    the speaker lookup, even though it contains "who is".
    """
    lower = message.lower()

    if any(w in lower for w in ["schedule", "session", "when", "tomorrow", "speaking"]):
        return _answer_schedule(message)
    if any(w in lower for w in ["venue", "room", "where", "parking", "wifi", "wi-fi"]):
        return _answer_venue_or_docs(message)
    if any(w in lower for w in ["register", "registration", "sign up", "ticket"]):
        return (
            "I can look up registration status if you give me the email "
            "address you registered with.",
            "get_registration_status",
        )
    if any(w in lower for w in ["speaker", "who is", "bio", "professor", "dr.", "tell me about"]):
        return _answer_speaker(message)

    UnansweredQuestion.objects.create(question_text=message)
    return (
        "I'm not sure which tool this needs yet - Day 3's real agent will "
        "reason about that. For now, try asking about the schedule, a "
        "speaker, or the venue.",
        None,
    )


def _answer_schedule(message: str):
    results = get_schedule()
    if not results:
        return "I don't have any sessions on record yet.", "get_schedule"

    lines = [
        f"- {s['title']} ({s['type']}) at {s['start_time'][:16].replace('T', ' ')} "
        f"in {s['venue']}, with {', '.join(s['speakers']) or 'TBA'}"
        for s in results[:5]
    ]
    reply = "Here's what's on the schedule:\n" + "\n".join(lines)
    return reply, "get_schedule"


def _answer_speaker(message: str):
    # crude name extraction: strip common question words, keep the rest
    for word in ["who is", "tell me about", "speaker", "bio of", "?"]:
        message = message.replace(word, "").replace(word.capitalize(), "")
    name = message.strip() or "Sharma"  # fallback for the "Speakers" quick chip

    result = get_speaker(name)
    if "error" in result:
        return result["error"], "get_speaker"

    session_titles = ", ".join(s["title"] for s in result["sessions"]) or "no sessions listed"
    reply = (
        f"{result['name']} ({result['title']}): {result['short_bio']} "
        f"Speaking at: {session_titles}."
    )
    return reply, "get_speaker"


def _answer_venue_or_docs(message: str):
    lower = message.lower()
    # Structured venue facts (room, building, capacity) -> DB tool.
    # Policy/logistics facts (parking, wifi) -> RAG, since that's unstructured text.
    if any(w in lower for w in ["parking", "wifi", "wi-fi"]):
        chunks = search_documents(message, top_k=1)
        if not chunks:
            return "I couldn't find that in the symposium documents.", "search_documents"
        return chunks[0]["text"], "search_documents"

    venues = get_venue()
    lines = [f"- {v['name']} ({v['building']}, capacity {v['capacity']})" for v in venues]
    reply = "Here are the venues:\n" + "\n".join(lines)
    return reply, "get_venue"
