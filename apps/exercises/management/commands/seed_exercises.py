from django.core.management.base import BaseCommand
from django.db import transaction

from apps.exercises.models import ExerciseTemplate
from apps.exercises.seed_data import EXERCISES


class Command(BaseCommand):
    help = "Create or update the built-in Persian exercise bank (idempotent)."

    @transaction.atomic
    def handle(self, *args, **opts):
        created = updated = 0
        for row in EXERCISES:
            data = dict(row)
            slug = data.pop("slug")
            obj, was_created = ExerciseTemplate.objects.get_or_create(slug=slug, defaults=data)
            if not was_created:
                for k, v in data.items():
                    setattr(obj, k, v)
            obj.is_custom = False
            obj.save()
            created += was_created
            updated += not was_created
        self.stdout.write(self.style.SUCCESS(f"exercises: {created} created, {updated} updated"))
