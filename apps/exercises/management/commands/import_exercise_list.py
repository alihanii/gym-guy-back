"""Load the exercise bank from data/exercises.csv.

    python manage.py import_exercise_list            # names, Persian titles, muscles
    python manage.py import_exercise_list --images   # also fetch each image once

data/exercises.csv is the single source of the bank. Columns:
    name_en       English name, e.g. "Bench Press (Barbell)". Also the row's id: renaming makes a new exercise.
    title_fa      Persian title shown in the app.
    muscle_group  Quadriceps, Chest, Full Body, Abdominals, Shoulders, Biceps, Glutes, Triceps, Upper Back,
                  Lats, Cardio, Hamstrings, Calves, Forearms, Traps, Neck, Lower Back, Adductors, Abductors, Other
    image         an https:// URL, or a file path relative to data/ (e.g. images/bench.jpg). May be empty.
Built-in exercises missing from the file are deleted; users' own exercises stay.
With --images, images are converted to WebP and saved to storage (media/ or S3),
so the app never links to the remote host. An image is fetched again only when
its value in the file changes, or with --force-images. Re-running is safe.
"""
import csv
import io
import re
import urllib.request
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from apps.exercises.models import ExerciseTemplate
from apps.exercises.taxonomy import Equipment, Muscle, TrackingType

DATA_DIR = Path(__file__).resolve().parents[4] / "data"
DATA = DATA_DIR / "exercises.csv"
SOURCE = "gym-list"

MUSCLE = {
    "Quadriceps": Muscle.QUADRICEPS, "Chest": Muscle.CHEST, "Full Body": Muscle.CARDIO, "Abdominals": Muscle.ABDOMINALS,
    "Shoulders": Muscle.SHOULDERS, "Biceps": Muscle.BICEPS, "Glutes": Muscle.GLUTES, "Triceps": Muscle.TRICEPS,
    "Upper Back": Muscle.UPPER_BACK, "Lats": Muscle.LATS, "Cardio": Muscle.CARDIO, "Hamstrings": Muscle.HAMSTRINGS,
    "Calves": Muscle.CALVES, "Forearms": Muscle.FOREARMS, "Traps": Muscle.TRAPS, "Neck": Muscle.NECK,
    "Lower Back": Muscle.LOWER_BACK, "Adductors": Muscle.ABDUCTORS_ADDUCTORS, "Abductors": Muscle.ABDUCTORS_ADDUCTORS,
    "Other": Muscle.CARDIO,
}

VARIANT_EQUIPMENT = {
    "Barbell": Equipment.BARBELL, "Trap bar": Equipment.BARBELL, "Dumbbell": Equipment.DUMBBELL,
    "Machine": Equipment.MACHINE, "Cable": Equipment.MACHINE, "Smith Machine": Equipment.MACHINE, "Smith": Equipment.MACHINE,
    "Pec Deck": Equipment.MACHINE, "Machine Plates": Equipment.MACHINE, "Weighted": Equipment.WEIGHTED_BODYWEIGHT,
    "Weighted Hyperextension": Equipment.WEIGHTED_BODYWEIGHT, "Assisted": Equipment.ASSISTED_BODYWEIGHT,
    "Band": Equipment.RESISTANCE_BAND, "band": Equipment.RESISTANCE_BAND, "Kettlebell": Equipment.KETTLEBELL,
    "Bodyweight": Equipment.REPS_ONLY, "Suspension": Equipment.REPS_ONLY, "Hyperextension": Equipment.REPS_ONLY,
    "Gironda": Equipment.REPS_ONLY, "Svend Press": Equipment.PLATE, "Sandbag": Equipment.OTHER,
    "Floors": Equipment.OTHER, "Steps": Equipment.OTHER,
}

NAME_EQUIPMENT = (
    ("kettlebell", Equipment.KETTLEBELL), ("dumbbell", Equipment.DUMBBELL), ("plate", Equipment.PLATE),
    ("cable", Equipment.MACHINE), ("machine", Equipment.MACHINE), ("pulldown", Equipment.MACHINE),
    ("pushdown", Equipment.MACHINE), ("pressdown", Equipment.MACHINE), ("seated row", Equipment.MACHINE),
    ("landmine", Equipment.BARBELL), ("ez bar", Equipment.BARBELL), ("deadlift", Equipment.BARBELL),
    ("clean", Equipment.BARBELL), ("snatch", Equipment.BARBELL), ("jerk", Equipment.BARBELL),
    ("rack pull", Equipment.BARBELL), ("thruster", Equipment.BARBELL), ("push press", Equipment.BARBELL),
    ("front squat", Equipment.BARBELL), ("zercher", Equipment.BARBELL), ("overhead squat", Equipment.BARBELL),
    ("t bar", Equipment.BARBELL), ("hack squat", Equipment.MACHINE), ("calf raise", Equipment.MACHINE),
    ("leg curl", Equipment.MACHINE), ("leg extension", Equipment.MACHINE), ("sled", Equipment.OTHER),
    ("wrist roller", Equipment.OTHER), ("ball", Equipment.OTHER), ("battle rope", Equipment.OTHER),
    ("farmers", Equipment.DUMBBELL), ("goblet", Equipment.DUMBBELL), ("hammer", Equipment.DUMBBELL),
    ("concentration", Equipment.DUMBBELL), ("drag curl", Equipment.BARBELL), ("21s", Equipment.BARBELL),
)

DISTANCE = re.compile(r"running|cycling|walking|swimming|rowing|treadmill|elliptical|hiking|skiing|ski erg|air bike|spinning|recumbent|sprints|stair|skating|snowboarding")
DURATION = re.compile(r"plank|wall sit|dead hang|hold|yoga|pilates|stretching|warm up|boxing|hiit|aerobics|climbing|battle ropes|jump rope|hollow rock")
CARRY = re.compile(r"farmers walk|suitcase carry|sled")


def split_name(name: str) -> tuple[str, str | None]:
    if name.endswith(")") and " (" in name:
        base, variant = name[:-1].rsplit(" (", 1)
        return base.strip(), variant.strip()
    return name.strip(), None


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:70]


def equipment_for(name: str, variant: str | None, muscle: str) -> str:
    if variant in VARIANT_EQUIPMENT:
        return VARIANT_EQUIPMENT[variant]
    n = name.lower()
    for word, eq in NAME_EQUIPMENT:
        if word in n:
            return eq
    if muscle == Muscle.CARDIO and DISTANCE.search(n):
        return Equipment.OTHER
    return Equipment.REPS_ONLY


def tracking_for(name: str, equipment: str) -> str:
    n = name.lower()
    if DISTANCE.search(n):
        return TrackingType.DISTANCE_DURATION
    if CARRY.search(n):
        return TrackingType.WEIGHT_DISTANCE
    if DURATION.search(n):
        return TrackingType.DURATION
    if equipment == Equipment.ASSISTED_BODYWEIGHT:
        return TrackingType.ASSISTED_BODYWEIGHT
    if equipment == Equipment.WEIGHTED_BODYWEIGHT:
        return TrackingType.BODYWEIGHT_REPS
    if equipment == Equipment.REPS_ONLY:
        return TrackingType.BODYWEIGHT_REPS if re.search(r"pull up|chin up|dip|muscle up", n) else TrackingType.REPS_ONLY
    return TrackingType.WEIGHT_REPS


def fetch_webp(src: str, base: Path, width: int) -> ContentFile:
    if src.startswith(("http://", "https://")):
        req = urllib.request.Request(src, headers={"User-Agent": "gym-guy-importer/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
    else:
        raw = (base / src).read_bytes()
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=80, method=5)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = "Make data/exercise_list.csv the exercise bank (Persian titles; --images downloads pictures once)."

    def add_arguments(self, parser):
        parser.add_argument("--csv", default=str(DATA))
        parser.add_argument("--images", action="store_true", help="fetch each row's image (URL or data/ path) into storage")
        parser.add_argument("--force-images", action="store_true")
        parser.add_argument("--width", type=int, default=480)

    def handle(self, csv, images, force_images, width, **_):
        import csv as csvlib
        base = Path(csv).resolve().parent
        with open(csv, newline="", encoding="utf-8-sig") as fh:
            rows = [r for r in csvlib.DictReader(fh) if (r.get("name_en") or "").strip()]

        keep, created, downloaded, failed = set(), 0, 0, []
        for r in rows:
            name, group, url = r["name_en"].strip(), (r.get("muscle_group") or "").strip(), (r.get("image") or "").strip()
            title_fa = (r.get("title_fa") or "").strip() or name
            _, variant = split_name(name)
            muscle = MUSCLE.get(group, Muscle.CARDIO)
            equipment = equipment_for(name, variant, muscle)
            obj, was_created = ExerciseTemplate.objects.get_or_create(
                slug=slugify(name),
                defaults={"title_en": name, "title_fa": title_fa, "equipment": equipment, "primary_muscle": muscle},
            )
            created += was_created
            obj.title_en = name
            obj.title_fa = title_fa
            obj.equipment = equipment
            obj.tracking_type = tracking_for(name, equipment)
            obj.primary_muscle = muscle
            obj.source = SOURCE
            obj.is_custom = False
            obj.listed = True
            if not url and obj.image_source:
                obj.thumbnail, obj.image_source = "", ""
            elif images and url and (force_images or not obj.thumbnail or obj.image_source != url):
                try:
                    obj.thumbnail.save(f"{obj.slug}.webp", fetch_webp(url, base, width), save=False)
                    obj.image_source = url
                    downloaded += 1
                except Exception as e:  # keep going; the app shows a placeholder
                    failed.append(f"{name}: {e}")
            obj.save()
            keep.add(obj.id)

        removed, _ = ExerciseTemplate.objects.filter(is_custom=False).exclude(id__in=keep).delete()
        renamed = self._unique_titles(keep)
        for f in failed:
            self.stderr.write(f"  image failed: {f}")
        with_image = ExerciseTemplate.objects.filter(id__in=keep).exclude(thumbnail="").count()
        self.stdout.write(self.style.SUCCESS(
            f"exercise list: {len(keep)} exercises ({created} new), {removed} others removed, {renamed} names made unique, "
            f"{downloaded} images downloaded, {len(failed)} failed, {with_image} of {len(keep)} have an image"
        ))

    def _unique_titles(self, ids) -> int:
        seen, changed = set(), 0
        for r in sorted(ExerciseTemplate.objects.filter(id__in=ids), key=lambda r: len(r.title_en)):
            if r.title_fa in seen:
                r.title_fa = f"{r.title_fa} ({r.title_en})"
                r.save(update_fields=["title_fa", "search_text"])
                changed += 1
            seen.add(r.title_fa)
        return changed
