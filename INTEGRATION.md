# Integration Contract — Symposium Assistant

This defines the exact seam between the two tracks so we can build independently
without breaking each other. If either side changes something listed here,
flag it to the other person before pushing.

---

## 1. The `/api/chat` endpoint — the main contract

**Request** (frontend → backend)
```json
POST /api/chat
Content-Type: application/json

{ "message": "who is speaking tomorrow?" }
```

**Success response** (backend → frontend)
```json
{
  "reply": "Here's what's on the schedule: ...",
  "tool_used": "get_schedule"
}
```
- `reply`: plain text, shown directly in the chat bubble. No markdown rendering on
  the frontend yet — keep it plain sentences/line breaks, not `**bold**` or `# headers`.
- `tool_used`: string naming which tool answered (e.g. `"get_schedule"`,
  `"get_speaker"`, `"search_documents"`), or `null` if no tool was needed.
  Shown as a small tag under the reply — this is what visually proves the
  "agent" is routing between sources, so try to always populate it.

**Error response** (backend → frontend)
```json
{ "error": "No speaker found matching 'xyz'." }
```
- Any 4xx/5xx status, or a 200 with an `error` key, is treated as an error by
  the frontend and shown as a retry-able error bubble.
- Don't change the key names (`reply`, `tool_used`, `error`) — the frontend
  JS reads exactly these three.

**This is the ONLY thing the frontend depends on.** Internals — which LLM,
what prompt, how tool-calling loops — are entirely up to you as long as this
shape comes out the other end.

---

## 2. Where your agent code plugs in

Current file: `chatui/views.py`, function `api_chat()`.

Right now it calls `_route_and_answer(message)`, which does simple keyword
matching (temporary, Day 2 stub). Replace the **body** of that function with
a call into your real agent, e.g.:

```python
from core.agent import run_agent  # your new file

def api_chat(request):
    ...
    reply, tool_used = run_agent(message)
    return JsonResponse({"reply": reply, "tool_used": tool_used})
```

**Please build your agent logic in a new file, `core/agent.py`, rather than
editing deep into `chatui/views.py` directly.** That file also has loading
state / error-handling logic on the frontend side that isn't related to your
work — keeping agent logic in its own file avoids merge conflicts on the same
lines.

---

## 3. The tool functions you call (already built, tested, in `core/tools.py`)

```python
get_schedule(date: str = None, track: str = None, speaker_name: str = None)
# date format: "YYYY-MM-DD". Returns list of session dicts, or [] if none.

get_speaker(name: str)
# partial name match. Returns dict, or {"error": "..."} if 0 or 2+ matches.

get_venue(name: str = None)
# omit name to list all venues. Returns dict or list of dicts.

get_registration_status(email: str)
# exact email match. Returns dict, or {"error": "..."} if not found.
```
Plus RAG search in `rag/search.py`:
```python
search_documents(query: str, top_k: int = 3, min_score: float = 0.3)
# returns list of {"text": ..., "source": ..., "score": ...}, or [] if nothing relevant
```

All tested against seeded data — see `core/test_tools_manually.py` for example
calls and expected output shapes. **Please don't change these function
signatures** without a heads-up — the frontend doesn't call them directly, but
changing return shapes could break how replies get formatted.

If you need a new tool (e.g. something for n8n integration), add a new
function to `core/tools.py` rather than modifying an existing one's behavior.

---

## 4. Data model (from Day 1, `core/models.py`)

`Venue`, `Speaker`, `Session`, `Registration` — field names are what
`core/tools.py` reads. If you need to add a field, that's safe (additive).
If you rename or remove a field that `tools.py` or `admin.py` already
references, those will break silently or loudly depending on the case —
please ping before doing that.

---

## 5. Environment / running it

Use what's already set up rather than a separate local setup:
- `requirements.txt` — add your LLM SDK (anthropic/openai) here, don't
  install it ad hoc
- `.env.example` — put your `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` var name
  here so both of us know what's expected; actual key goes in your own
  untracked `.env`
- `docker-compose.yml` — if it works in Docker for you, it'll work the same
  way for me and in deployment. Worth testing against this instead of only
  bare `runserver`.

---

## 6. Suggested workflow to avoid end-of-project surprises

- Short daily sync: "here's what I changed, here's what I need from you."
- Whoever changes something in section 1, 3, or 4 above (the shared
  contract) flags it immediately — those are the only things that can break
  the other person's work silently.
- Merge/pull frequently rather than working in isolation for days at a time.
