from django.conf import settings
from django.db import models
from django.utils import timezone


class Routine(models.Model):
    """A reusable workout day. Coach programs are injected here as routines."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="routines")
    program = models.ForeignKey(
        "coaching.Program", null=True, blank=True, on_delete=models.CASCADE, related_name="routines"
    )
    day_index = models.PositiveSmallIntegerField(default=0)
    title = models.CharField(max_length=120)
    folder = models.CharField(max_length=60, blank=True, default="")
    exercises = models.JSONField(default=list)  # list of template blocks
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["program_id", "day_index", "-updated_at"]


class WorkoutLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workouts")
    program = models.ForeignKey("coaching.Program", null=True, blank=True, on_delete=models.SET_NULL, related_name="logs")
    routine = models.ForeignKey(Routine, null=True, blank=True, on_delete=models.SET_NULL, related_name="logs")
    title = models.CharField(max_length=120)
    started_at = models.DateTimeField()
    duration_seconds = models.PositiveIntegerField()
    exercises = models.JSONField(default=list)  # performed blocks with sets
    exercise_ids = models.JSONField(default=list)  # sorted slugs, for "previous set" lookups
    actual_heatmap = models.JSONField(default=dict)
    total_volume_kg = models.FloatField(default=0)
    total_sets = models.PositiveIntegerField(default=0)
    records = models.JSONField(default=list)  # PRs broken in this session
    notes = models.TextField(blank=True)
    coach_feedback = models.TextField(blank=True)
    completed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-completed_at"]


class RecordKind(models.TextChoices):
    EST_1RM = "est_1rm", "یک تکرار بیشینه تخمینی"
    MAX_WEIGHT = "max_weight", "سنگین‌ترین وزنه"
    MAX_VOLUME = "max_volume", "بیشترین حجم ست"
    MAX_REPS = "max_reps", "بیشترین تکرار"


class PersonalRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="records")
    exercise_id = models.CharField(max_length=80)
    kind = models.CharField(max_length=12, choices=RecordKind.choices)
    value = models.FloatField()
    workout = models.ForeignKey(WorkoutLog, on_delete=models.CASCADE, related_name="+")
    achieved_at = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "exercise_id", "kind"], name="one_record_per_kind")]
