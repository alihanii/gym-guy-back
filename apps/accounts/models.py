from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    ATHLETE = "athlete", "ورزشکار"
    COACH = "coach", "مربی"
    BOTH = "both", "هر دو"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, phone, password=None, **extra):
        if not phone:
            raise ValueError("phone is required")
        user = self.model(phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.BOTH)
        return self.create_user(phone, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.ATHLETE)
    # Height, weight, body-fat, tape measurements… shape is owned by the frontend.
    metrics = models.JSONField(default=dict, blank=True)
    unit = models.CharField(max_length=2, choices=[("kg", "kg"), ("lb", "lb")], default="kg")
    is_private = models.BooleanField(default=False)  # hide my workouts from the public feed
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["name"]

    @property
    def is_coach(self) -> bool:
        return self.role in (Role.COACH, Role.BOTH)

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Measurement(models.Model):
    """One body check-in: weight and tape measurements on a date."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="measurements")
    date = models.DateField(default=timezone.localdate)
    weight_kg = models.FloatField(null=True, blank=True)
    body_fat = models.FloatField(null=True, blank=True)
    waist_cm = models.FloatField(null=True, blank=True)
    chest_cm = models.FloatField(null=True, blank=True)
    arm_cm = models.FloatField(null=True, blank=True)
    thigh_cm = models.FloatField(null=True, blank=True)
    hip_cm = models.FloatField(null=True, blank=True)
    notes = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["-date", "-id"]
