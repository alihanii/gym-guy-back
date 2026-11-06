"""Exercise taxonomy shared by the API, the seed and the heatmap engine."""
from django.db import models


class Equipment(models.TextChoices):
    BARBELL = "barbell", "هالتر"
    DUMBBELL = "dumbbell", "دمبل"
    MACHINE = "machine", "دستگاه و سیم‌کش"
    WEIGHTED_BODYWEIGHT = "weighted_bodyweight", "وزن بدن (+وزنه)"
    ASSISTED_BODYWEIGHT = "assisted_bodyweight", "وزن بدن (کمکی)"
    REPS_ONLY = "reps_only", "وزن بدن (بدون وسیله)"
    KETTLEBELL = "kettlebell", "کتل‌بل"
    PLATE = "plate", "صفحه هالتر"
    RESISTANCE_BAND = "resistance_band", "کش ورزشی"
    OTHER = "other", "سایر / هوازی"


class Muscle(models.TextChoices):
    CHEST = "chest", "سینه"
    SHOULDERS = "shoulders", "سرشانه"
    BICEPS = "biceps", "جلوبازو"
    FOREARMS = "forearms", "ساعد"
    ABDOMINALS = "abdominals", "شکم و میان‌تنه"
    LATS = "lats", "زیربغل"
    TRAPS = "traps", "کول"
    UPPER_BACK = "upper_back", "پشت میانی"
    LOWER_BACK = "lower_back", "فیله کمر"
    TRICEPS = "triceps", "پشت بازو"
    NECK = "neck", "گردن"
    QUADRICEPS = "quadriceps", "چهارسر ران"
    HAMSTRINGS = "hamstrings", "همسترینگ"
    GLUTES = "glutes", "باسن"
    CALVES = "calves", "ساق پا"
    ABDUCTORS_ADDUCTORS = "abductors_adductors", "داخل و خارج ران"
    CARDIO = "cardio", "هوازی / کل بدن"


class TrackingType(models.TextChoices):
    WEIGHT_REPS = "weight_reps", "وزن و تکرار"
    BODYWEIGHT_REPS = "bodyweight_reps", "وزن بدن و تکرار"
    ASSISTED_BODYWEIGHT = "assisted_bodyweight", "وزن کمکی و تکرار"
    DURATION = "duration", "زمان"
    DURATION_WEIGHT = "duration_weight", "زمان و وزن"
    DISTANCE_DURATION = "distance_duration", "مسافت و زمان"
    WEIGHT_DISTANCE = "weight_distance", "وزن و مسافت"
    REPS_ONLY = "reps_only", "فقط تکرار"


class SetType(models.TextChoices):
    WARMUP = "warmup", "W"
    NORMAL = "normal", "N"
    DROPSET = "dropset", "D"
    FAILURE = "failure", "F"


class InjuryTag(models.TextChoices):
    LOWER_BACK = "lower_back", "دیسک / درد کمر"
    KNEE = "knee", "آسیب زانو / مینیسک"
    SHOULDER = "shoulder", "گیرافتادگی / آسیب شانه"
    ELBOW = "elbow", "درد آرنج"
    WRIST = "wrist", "درد مچ دست"
    NECK = "neck", "دیسک / درد گردن"
    HIP = "hip", "درد لگن"
    ANKLE = "ankle", "آسیب مچ پا"


PRIMARY_WEIGHT = 1.0
SECONDARY_WEIGHT = 0.5
