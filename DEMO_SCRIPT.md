# Demo Day Script

A suggested order to run live, each question chosen to show something
specific. Every question below was tested against the real app while
building it - these are known-working, not guesses.

## Suggested order (use the chips where noted - faster and typo-proof)

**1. Open with the concept, not the UI.** Before touching the keyboard, say
in one sentence what makes this an *agent* rather than a chatbot: it looks
at the question, decides which data source answers it, and only then
responds - schedule and venue are database lookups, policy questions go
through document search, and anything it can't match gets logged instead
of guessing.

**2. Click the "Schedule" chip** → *"Who is speaking tomorrow and where?"*
- Shows: a real multi-field DB query (time + venue + speaker joined
  together), and the `tool used: get_schedule` tag under the reply -
  point at that tag, it's the visible proof of routing.

**3. Type:** *"Tell me about Dr. Sharma"*
- Shows: a second tool (`get_speaker`), and that the same person appears
  correctly across multiple sessions (she's in both a keynote and the
  closing panel) - demonstrates the data isn't flat/fake.

**4. Click the "Venue" chip** → *"Where is the venue and is there parking?"*
- Shows: this one question needs two different tools - venue list from
  the database, parking info from document search (RAG) - because
  parking policy isn't structured data, it's a sentence in a FAQ file.
  This is the best single question for explaining the RAG/DB boundary
  if a judge asks about it.

**5. Type something it genuinely can't answer:** *"What's the weather like
this weekend?"*
- Shows: it doesn't guess or hallucinate - it says so honestly. If asked,
  mention this gets logged to a review queue (`UnansweredQuestion`,
  visible in Django admin) so organizers can see real gaps in coverage
  after the event, not just during it.

**6. Click the speaker icon (top right) to enable voice**, then click the
mic and ask a question out loud.
- Only do this if you've confirmed mic access works on the demo network
  beforehand (see Known Limitations below) - don't discover it live.

**7. Close by opening `/admin`** and showing the Unanswered Questions list
with real entries from the demo you just ran - ties the "agent reasons
about what it knows" claim back to something concrete.

## If a judge asks to see something break

Good, don't dodge it - show the fallback case again (step 5) and explain
it's intentional: an honest "I don't know" beats a confident wrong answer,
and the logging means that gap gets reviewed later rather than silently
recurring.

## Known limitations - have an answer ready, don't get caught off guard

- **Tool routing is currently keyword-based, not full LLM reasoning.**
  Be upfront about this if asked directly: "the tool-selection layer is
  being upgraded to real LLM-based reasoning; what's live right now
  proves the architecture and all the underlying data tools work
  correctly end to end."
- **Voice input needs HTTPS or localhost**, and genuine internet access
  on the demo machine (it calls Google's speech service). Test on the
  actual demo network beforehand - don't assume the venue's wifi allows
  it.
- **RAG document search** needs `index.pkl` built at least once
  (`python manage.py seed_data` doesn't do this - run the RAG build
  separately, see `rag/build_index.py`). Confirm this was run on the
  live deployment before demo day, or "is there parking" will answer
  "I couldn't find that" instead of the real policy answer.

## Rehearsal checklist

- [ ] Run every question above against the actual deployed URL, not
      just localhost, at least once before demo day
- [ ] Confirm `rag/index.pkl` exists on the live server (RAG answers work)
- [ ] Confirm demo data is seeded (`python manage.py seed_data` was run)
- [ ] Test on the actual venue wifi if possible, especially for voice
- [ ] Have a backup: a screen recording of a successful run, in case
      live network/demo issues come up
