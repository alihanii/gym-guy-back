"""Remove every built-in exercise so the bank starts empty.

    python manage.py clear_exercise_bank

Exercises users created themselves (is_custom) are kept. Image files are left
in storage; only the database rows go.
"""
from django.core.management.base import BaseCommand

from apps.exercises.models import ExerciseTemplate


class Command(BaseCommand):
    help = "Delete all built-in exercises (keeps users' own)."

    def handle(self, **_):
        n, _ = ExerciseTemplate.objects.filter(is_custom=False).delete()
        self.stdout.write(self.style.SUCCESS(f"exercise bank cleared: {n} built-in exercises removed"))
