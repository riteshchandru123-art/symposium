# RAG Reindexing — Automation Approach

## What changed from the original plan

The original Day 5 plan routed reindexing through n8n:
`Django admin -> webhook -> n8n -> HTTP call back -> Django`.

That adds an external service, an account to manage, and a network hop
that can fail — without n8n actually doing anything n8n is good at
(no branching, no scheduling, no multi-service orchestration). It was
just relaying a call back to the same app that sent it.

**Simplified to**: the Django admin action calls the reindex logic
directly, in-process. No webhook, no external service, no n8n involved.

## How it works now

1. Admin edits a Speaker/Venue/Session/Registration in Django admin
2. Selects the row(s), picks **"Rebuild RAG index now"** from the Actions
   dropdown, clicks **Go**
3. `core/admin.py`'s `trigger_reindex()` calls `run_reindex()`
   (`core/reindex.py`) directly — same function that used to be called
   via the `/api/reindex` HTTP endpoint, just invoked in-process instead
4. Success/failure shows immediately as a Django admin message

## The `/api/reindex` HTTP endpoint is still there, and still useful

It wasn't removed — it's kept as an optional automation hook for anyone
who *does* want external triggering later, without needing n8n:

**Option A — a cron job on the EC2 instance** (simplest possible
automation, no extra service at all):
```bash
# rebuild the index every night at 2am
crontab -e
# add this line:
0 2 * * * curl -s -X POST http://localhost:8000/api/reindex -H "X-Reindex-Secret: <your REINDEX_SECRET>"
```

**Option B — n8n, if a later step genuinely needs it** (e.g. reindexing
as one step inside a larger workflow that also does something n8n is
actually suited for, like conditional branching across services) — the
endpoint is already secret-protected and ready to be called from
anywhere, n8n included.

## Where n8n is still worth using in this project

Day 6's planned workflow — notifying organizers (Slack/email) when the
agent can't answer a question — is a better fit for n8n than reindexing
ever was. That's genuinely outside what Django does natively, and is
exactly the kind of "route data to an external service" task n8n exists
for. `requests` stays in `requirements.txt` for when that's built.
