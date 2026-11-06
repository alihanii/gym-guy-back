import secrets

from django.conf import settings
from django.db import models


class Goal(models.TextChoices):
    FAT_LOSS = "fat_loss", "کاهش وزن"
    HYPERTROPHY = "hypertrophy", "عضله‌سازی"
    STRENGTH = "strength", "قدرت"
    FITNESS = "fitness", "آمادگی جسمانی"


class Client(models.Model):
    """A coach's file on one trainee. Linked to an athlete account once they redeem a code."""

    coach = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="clients")
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="coach_files"
    )
    name = models.CharField(max_length=120)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    experience_months = models.PositiveSmallIntegerField(null=True, blank=True)
    goal = models.CharField(max_length=16, choices=Goal.choices, default=Goal.HYPERTROPHY)
    days_per_week = models.PositiveSmallIntegerField(default=3)
    injury_tags = models.JSONField(default=list, blank=True)  # list[InjuryTag]
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ProgramStatus(models.TextChoices):
    DRAFT = "draft", "پیش‌نویس"
    PENDING_INVITE = "pending_invite", "در انتظار شاگرد"
    ACTIVE = "active", "فعال"
    ARCHIVED = "archived", "بایگانی"


def generate_invite_code() -> str:
    """Six random digits that no other program uses."""
    while True:
        code = f"{secrets.randbelow(1_000_000):06d}"
        if not Program.objects.filter(invite_code=code).exists():
            return code


class Program(models.Model):
    coach = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="programs")
    client = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL, related_name="programs")
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_programs"
    )
    title = models.CharField(max_length=120)
    status = models.CharField(max_length=16, choices=ProgramStatus.choices, default=ProgramStatus.DRAFT)
    invite_code = models.CharField(max_length=6, unique=True, null=True, blank=True)
    injury_tags = models.JSONField(default=list, blank=True)
    # {"days": [{"title": "...", "exercises": [<block>, ...]}]} — see workouts.schemas
    workouts = models.JSONField(default=dict)
    diet_plan = models.JSONField(null=True, blank=True)
    planned_heatmap = models.JSONField(default=dict, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    @property
    def days(self) -> list[dict]:
        return (self.workouts or {}).get("days", [])

    @property
    def invite_link(self) -> str | None:
        if not self.invite_code:
            return None
        return f"{settings.FRONTEND_URL.rstrip('/')}/join/{self.invite_code}"
