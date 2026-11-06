from django.conf import settings
from django.db import models

from .text import normalize_fa
from .taxonomy import Equipment, Muscle, TrackingType


class ExerciseTemplate(models.Model):
    # Stable, human-readable id, e.g. "bench_press_barbell". The AI importer
    # and stored workouts reference exercises by this slug.
    slug = models.SlugField(max_length=80, unique=True)
    title_en = models.CharField(max_length=120)
    title_fa = models.CharField(max_length=120)
    persian_aliases = models.JSONField(default=list, blank=True)  # list[str]
    equipment = models.CharField(max_length=24, choices=Equipment.choices)
    tracking_type = models.CharField(max_length=24, choices=TrackingType.choices, default=TrackingType.WEIGHT_REPS)
    primary_muscle = models.CharField(max_length=24, choices=Muscle.choices)
    secondary_muscles = models.JSONField(default=list, blank=True)  # list[Muscle]
    injury_warnings = models.JSONField(default=list, blank=True)  # list[InjuryTag]
    thumbnail = models.ImageField(upload_to="exercises/thumbs/", blank=True)  # start position
    image_end = models.ImageField(upload_to="exercises/thumbs/", blank=True)  # end position
    instructions = models.JSONField(default=list, blank=True)  # English steps from the source dataset
    level = models.CharField(max_length=16, blank=True)
    category = models.CharField(max_length=24, blank=True)
    source = models.CharField(max_length=24, default="curated")  # curated | free-exercise-db | user
    video = models.FileField(upload_to="exercises/videos/", blank=True)
    is_custom = models.BooleanField(default=False)
    # False hides a built-in from the bank and picker; workouts that already use it still resolve.
    listed = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="custom_exercises"
    )
    # Normalised Persian + English + aliases, used for fast `icontains` search.
    search_text = models.TextField(editable=False, default="")

    class Meta:
        ordering = ["title_fa"]

    def save(self, *args, **kwargs):
        parts = [self.title_fa, self.title_en, *self.persian_aliases]
        self.search_text = " | ".join(normalize_fa(p) for p in parts)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title_fa} / {self.title_en}"
