"""
Quick manual verification of core/tools.py against seeded data.
Run: python manage.py shell < core/test_tools_manually.py
(or paste into `python manage.py shell`)
"""
import json
from datetime import timedelta
from django.utils import timezone
from core.tools import get_schedule, get_speaker, get_venue, get_registration_status


def show(label, result):
    print(f"\n--- {label} ---")
    print(json.dumps(result, indent=2)[:800])


# 1. Schedule for "tomorrow" (matches seed_data's relative date)
tomorrow = (timezone.now() + timedelta(days=1)).date().isoformat()
show(f"get_schedule(date={tomorrow!r})", get_schedule(date=tomorrow))

# 2. Schedule filtered by track
show("get_schedule(track='AI/ML')", get_schedule(track="AI/ML"))

# 3. Schedule filtered by speaker name (partial match)
show("get_schedule(speaker_name='Sharma')", get_schedule(speaker_name="Sharma"))

# 4. Speaker lookup - single match
show("get_speaker('Sharma')", get_speaker("Sharma"))

# 5. Speaker lookup - no match
show("get_speaker('Nonexistent')", get_speaker("Nonexistent Person"))

# 6. Speaker lookup - ambiguous (both contain 'Dr.')
show("get_speaker('Dr.')", get_speaker("Dr."))

# 7. Venue lookup - specific
show("get_venue('Auditorium')", get_venue("Auditorium"))

# 8. Venue lookup - list all
show("get_venue() [list all]", get_venue())

# 9. Venue lookup - no match
show("get_venue('Nonexistent Room')", get_venue("Nonexistent Room"))

# 10. Registration lookup - existing
show("get_registration_status('student@example.edu')",
     get_registration_status("student@example.edu"))

# 11. Registration lookup - not found
show("get_registration_status('nobody@example.edu')",
     get_registration_status("nobody@example.edu"))

print("\n\nAll tool functions executed without raising exceptions.")
