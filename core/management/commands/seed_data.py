"""
Populates the database with realistic demo data for the symposium.

Usage:
    python manage.py seed_data

Safe to re-run: clears existing data first.

Note: speaker names here intentionally match rag/documents/speaker_bios.txt
so a question like "tell me about Dr. Sharma's session and background" pulls
consistent info from both the DB (session/time/room) and RAG (bio detail).
"""

from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Venue, Speaker, Session, Registration


class Command(BaseCommand):
    help = "Seed the database with demo symposium data"

    def handle(self, *args, **options):
        self.stdout.write("Clearing existing data...")
        Registration.objects.all().delete()
        Session.objects.all().delete()
        Speaker.objects.all().delete()
        Venue.objects.all().delete()

        # --- Venues ---
        auditorium = Venue.objects.create(
            name="Main Auditorium", building="Block A", floor="Ground",
            capacity=300, notes="Wheelchair accessible"
        )
        hall_b = Venue.objects.create(
            name="Seminar Hall B", building="Block A", floor="1st Floor",
            capacity=80
        )
        lab_c = Venue.objects.create(
            name="Workshop Lab C", building="Block B", floor="2nd Floor",
            capacity=40, notes="Requires laptop"
        )

        # --- Speakers (match rag/documents/speaker_bios.txt) ---
        sharma = Speaker.objects.create(
            name="Dr. Ananya Sharma", title="Professor, IISc Bengaluru",
            short_bio="ML researcher focused on reinforcement learning for robotics."
        )
        verma = Speaker.objects.create(
            name="Rahul Verma", title="Founder & CEO, NeuralCraft",
            short_bio="Building AI diagnostic tools for rural healthcare."
        )
        nair = Speaker.objects.create(
            name="Dr. Priya Nair", title="Lab Lead, IIT Bombay",
            short_bio="Cognitive scientist studying LLM reasoning vs human cognition."
        )
        iyer = Speaker.objects.create(
            name="Karthik Iyer", title="Data Engineering Lead, Fintech",
            short_bio="Real-time fraud detection pipelines at scale."
        )
        krishnan = Speaker.objects.create(
            name="Dr. Meera Krishnan", title="AI Policy Advisor",
            short_bio="Researches bias and ethics in generative AI systems."
        )

        # --- Sessions ---
        # "Tomorrow" relative to seed-run time, so the demo question
        # ("who's speaking tomorrow?") stays realistic when you run this.
        tomorrow = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)

        s1 = Session.objects.create(
            title="Reinforcement Learning for Real-World Robotics",
            session_type="keynote", venue=auditorium,
            start_time=tomorrow, end_time=tomorrow + timedelta(hours=1),
            track="AI/ML",
            description="Opening keynote on applying RL beyond simulation."
        )
        s1.speakers.add(sharma)

        s2_start = tomorrow + timedelta(hours=1, minutes=30)
        s2 = Session.objects.create(
            title="AI in Rural Healthcare: Lessons from the Field",
            session_type="talk", venue=hall_b,
            start_time=s2_start, end_time=s2_start + timedelta(minutes=45),
            track="AI/ML",
        )
        s2.speakers.add(verma)

        s3_start = tomorrow + timedelta(hours=3)
        s3 = Session.objects.create(
            title="Do LLMs Reason Like Humans?",
            session_type="talk", venue=auditorium,
            start_time=s3_start, end_time=s3_start + timedelta(minutes=45),
            track="Cognitive Science",
        )
        s3.speakers.add(nair)

        s4_start = tomorrow + timedelta(hours=4)
        s4 = Session.objects.create(
            title="Building Real-Time Fraud Detection Pipelines",
            session_type="workshop", venue=lab_c,
            start_time=s4_start, end_time=s4_start + timedelta(hours=1, minutes=30),
            track="Data Engineering", capacity=40,
        )
        s4.speakers.add(iyer)

        s5_start = tomorrow + timedelta(hours=5, minutes=30)
        s5 = Session.objects.create(
            title="Bias and Fairness in Generative AI Systems",
            session_type="talk", venue=hall_b,
            start_time=s5_start, end_time=s5_start + timedelta(minutes=45),
            track="Policy",
        )
        s5.speakers.add(krishnan)

        # --- Day 2 sessions ---
        day2 = tomorrow + timedelta(days=1)

        s6_start = day2.replace(hour=9, minute=30)
        s6 = Session.objects.create(
            title="Scaling Data Pipelines for Real-Time ML",
            session_type="keynote", venue=auditorium,
            start_time=s6_start, end_time=s6_start + timedelta(hours=1),
            track="Data Engineering",
            description="Day 2 opening keynote on infrastructure for live ML systems.",
        )
        s6.speakers.add(iyer)

        s7_start = day2.replace(hour=11, minute=0)
        s7 = Session.objects.create(
            title="Interpretability: Why Did the Model Say That?",
            session_type="talk", venue=auditorium,
            start_time=s7_start, end_time=s7_start + timedelta(minutes=45),
            track="Cognitive Science",
        )
        s7.speakers.add(nair)

        s8_start = day2.replace(hour=12, minute=0)
        s8 = Session.objects.create(
            title="Hands-On: Building a Diagnostic Model from Scratch",
            session_type="workshop", venue=lab_c,
            start_time=s8_start, end_time=s8_start + timedelta(hours=1, minutes=30),
            track="AI/ML", capacity=40,
        )
        s8.speakers.add(verma)

        s9_start = day2.replace(hour=15, minute=30)
        s9 = Session.objects.create(
            title="Panel: Regulating AI Without Killing Innovation",
            session_type="panel", venue=auditorium,
            start_time=s9_start, end_time=s9_start + timedelta(hours=1),
            track="Policy",
            description="Closing panel with speakers from both days.",
        )
        s9.speakers.add(krishnan, sharma, nair)

        # --- Sample registrations ---
        reg1 = Registration.objects.create(
            student_name="Sample Student", email="student@example.edu", status="confirmed"
        )
        reg1.registered_sessions.add(s1, s4, s8)

        reg2 = Registration.objects.create(
            student_name="Aditi Rao", email="aditi.rao@example.edu", status="confirmed"
        )
        reg2.registered_sessions.add(s1, s6, s9)

        reg3 = Registration.objects.create(
            student_name="Vikram Nath", email="vikram.nath@example.edu", status="waitlisted"
        )
        reg3.registered_sessions.add(s4)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {Venue.objects.count()} venues, "
            f"{Speaker.objects.count()} speakers, "
            f"{Session.objects.count()} sessions, "
            f"{Registration.objects.count()} registrations."
        ))
