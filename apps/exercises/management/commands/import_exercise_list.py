"""Make data/exercise_list.csv the exercise bank.

    python manage.py import_exercise_list

Each name in the list becomes one listed exercise with a Persian title.
- A curated row with the same exercise is reused (its slug, Persian name and
  injury tags stay), so saved workouts and programs keep working.
- Otherwise a new row is created. Images are borrowed from the closest
  free-exercise-db row when one matches well; the rest stay imageless.
- Every other built-in row is unlisted: hidden from the bank and the picker,
  still resolvable by slug for old workouts. Custom exercises are untouched.
Re-running is safe.
"""
import csv
import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.exercises.exercise_list_fa import persian_title, split_name
from apps.exercises.models import ExerciseTemplate
from apps.exercises.taxonomy import Equipment, Muscle, TrackingType

DATA = Path(__file__).resolve().parents[2] / "data" / "exercise_list.csv"
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

# Names in the list whose curated row is spelled differently.
CURATED_ALIAS = {
    "Ab Wheel": "ab_wheel", "Elliptical Trainer": "elliptical", "Farmers Walk": "farmers_walk", "T Bar Row": "t_bar_row",
    "EZ Bar Biceps Curl": "ez_bar_curl", "Bench Press - Close Grip (Barbell)": "close_grip_bench_press",
    "Butterfly (Pec Deck)": "chest_fly_machine", "Cable Fly Crossovers": "cable_crossover",
    "Rear Delt Reverse Fly (Dumbbell)": "rear_delt_fly_dumbbell", "Rear Delt Reverse Fly (Machine)": "reverse_fly_machine",
    "Seated Incline Curl (Dumbbell)": "incline_curl_dumbbell", "Incline Bench Press (Dumbbell)": "incline_press_dumbbell",
    "Incline Chest Fly (Dumbbell)": "incline_fly_dumbbell", "Seated Overhead Press (Dumbbell)": "seated_shoulder_press_dumbbell",
    "Seated Shoulder Press (Machine)": "shoulder_press_machine", "Skullcrusher (Barbell)": "skull_crusher_ez",
    "Seated Cable Row - V Grip (Cable)": "seated_cable_row", "Straight Arm Lat Pulldown (Cable)": "straight_arm_pulldown",
    "Russian Twist (Weighted)": "russian_twist_plate", "Plate Front Raise": "front_raise_plate",
    "Chest Dip (Weighted)": "weighted_dip", "Chest Dip (Assisted)": "assisted_dip",
    "Standing Cable Glute Kickbacks": "cable_kickback", "Calf Press (Machine)": "calf_press_leg_press",
    "Seated Calf Raise": "seated_calf_raise", "Seated Wrist Curl (Barbell)": "wrist_curl_barbell",
    "Recumbent Bike": "stationary_bike", "Bulgarian Split Squat (Dumbbell)": "bulgarian_split_squat",
    "Dumbbell Step Up": "step_up_dumbbell", "Preacher Curl (Barbell)": "preacher_curl",
    "Front Squat": "front_squat_barbell", "Hack Squat (Machine)": "hack_squat", "Rack Pull": "rack_pull",
    "Sumo Deadlift": "sumo_deadlift", "Triceps Pushdown": "triceps_pushdown_cable",
    "Overhead Triceps Extension (Cable)": "overhead_triceps_extension_cable",
    "Triceps Extension (Dumbbell)": "overhead_triceps_extension_dumbbell", "Seated Row (Machine)": "seated_row_machine",
    "Cable Core Pallof Press": "pallof_press_band", "Face Pull": "face_pull_cable", "Back Extension (Hyperextension)": "hyperextension",
    "Squat (Bodyweight)": "bodyweight_squat", "Plate Curl": "plate_curl", "Upright Row (Barbell)": "upright_row_barbell",
}

DISTANCE = re.compile(r"running|cycling|walking|swimming|rowing|treadmill|elliptical|hiking|skiing|ski erg|air bike|spinning|recumbent|sprints|stair|skating|snowboarding")
DURATION = re.compile(r"plank|wall sit|dead hang|hold|yoga|pilates|stretching|warm up|boxing|hiit|aerobics|climbing|battle ropes|jump rope|hollow rock")
CARRY = re.compile(r"farmers walk|suitcase carry|sled")

STOP = {"the", "and", "on", "to", "of", "with", "a"}
SYN = {"bicep": "biceps", "tricep": "triceps", "pushup": "push", "pushups": "push", "ups": "up", "flye": "fly", "flys": "fly",
       "flyes": "fly", "situp": "sit", "pullup": "pull", "pulldowns": "pulldown", "raises": "raise", "curls": "curl",
       "rows": "row", "bands": "band", "squats": "squat", "lunges": "lunge", "jumps": "jump", "kicks": "kick", "dips": "dip",
       "crunches": "crunch", "extensions": "extension", "slams": "slam", "skullcrushers": "skullcrusher",
       "lying": "lying", "ez": "ez", "kettlebells": "kettlebell", "dumbbells": "dumbbell",
       "smith": "smith", "deck": "pec", "hamstrings": "hamstring", "knees": "knee", "taps": "tap", "hydrants": "hydrant"}


EQUIPMENT_WORDS = {"barbell", "dumbbell", "cable", "machine", "smith", "band", "kettlebell", "plate", "leverage", "trap", "suspended", "weighted", "assisted"}
VARIANT_TOKENS = {
    "Barbell": {"barbell"}, "Dumbbell": {"dumbbell"}, "Cable": {"cable"}, "Machine": {"machine", "leverage"},
    "Smith Machine": {"smith"}, "Smith": {"smith"}, "Band": {"band"}, "band": {"band"}, "Kettlebell": {"kettlebell"},
    "Weighted": {"weighted"}, "Assisted": {"assisted"}, "Suspension": {"suspended"}, "Trap bar": {"trap"},
}


def tokens(s: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", s.lower().replace("push-up", "push up").replace("pull-up", "pull up"))
    return {SYN.get(w, w) for w in words if w not in STOP}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:70]


def equipment_for(name: str, variant: str | None, muscle: str) -> str:
    if variant in VARIANT_EQUIPMENT:
        return VARIANT_EQUIPMENT[variant]
    n = name.lower()
    for word, eq in (("kettlebell", Equipment.KETTLEBELL), ("dumbbell", Equipment.DUMBBELL), ("plate", Equipment.PLATE),
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
                     ("concentration", Equipment.DUMBBELL), ("drag curl", Equipment.BARBELL), ("21s", Equipment.BARBELL)):
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


class Command(BaseCommand):
    help = "Make the curated gym exercise list (data/exercise_list.csv) the exercise bank, with Persian titles."

    def add_arguments(self, parser):
        parser.add_argument("--csv", default=str(DATA))
        parser.add_argument("--verbose-matches", action="store_true")

    @transaction.atomic
    def handle(self, csv, verbose_matches, **_):
        import csv as csvlib
        with open(csv, newline="", encoding="utf-8") as fh:
            rows = [(r["name"].strip(), r["muscle_group"].strip()) for r in csvlib.DictReader(fh) if r.get("name")]

        builtin = list(ExerciseTemplate.objects.filter(is_custom=False))
        curated_by_en = {r.title_en.lower(): r for r in builtin if r.source == "curated"}
        by_slug = {r.slug: r for r in builtin}
        donors = [(tokens(r.title_en), r) for r in builtin if r.source == "free-exercise-db" and r.thumbnail]

        keep, created, reused, imaged = set(), 0, 0, 0
        for name, group in rows:
            base, variant = split_name(name)
            muscle = MUSCLE.get(group, Muscle.CARDIO)
            obj = by_slug.get(CURATED_ALIAS.get(name, "")) or curated_by_en.get(name.lower())
            if obj and obj.id not in keep:
                reused += 1
                if name != obj.title_en and name not in obj.persian_aliases:
                    obj.persian_aliases = [*obj.persian_aliases, name]
            else:
                slug = slugify(name)
                obj = by_slug.get(slug)
                if obj is None or (obj.source != SOURCE):
                    slug = slug if slug not in by_slug else f"{slug}_gl"
                    obj = by_slug.get(slug) or ExerciseTemplate(slug=slug)
                created += obj.pk is None
                equipment = equipment_for(name, variant, muscle)
                obj.title_en = name
                obj.title_fa = persian_title(name)
                obj.equipment = equipment
                obj.tracking_type = tracking_for(name, equipment)
                obj.primary_muscle = muscle
                obj.source = SOURCE
            if not obj.thumbnail:
                donor = self._donor(name, base, variant, donors)
                if donor:
                    obj.thumbnail.name = donor.thumbnail.name
                    obj.image_end.name = donor.image_end.name
                    obj.instructions = obj.instructions or donor.instructions
                    if not obj.secondary_muscles:
                        obj.secondary_muscles = [m for m in donor.secondary_muscles if m != obj.primary_muscle]
                    imaged += 1
                    if verbose_matches:
                        self.stdout.write(f"  {name}  <-  {donor.title_en}")
            obj.listed = True
            obj.save()
            keep.add(obj.id)
            by_slug[obj.slug] = obj

        hidden = ExerciseTemplate.objects.filter(is_custom=False).exclude(id__in=keep).update(listed=False)
        renamed = self._unique_titles(keep)
        with_image = ExerciseTemplate.objects.filter(id__in=keep).exclude(thumbnail="").count()
        self.stdout.write(self.style.SUCCESS(
            f"exercise list: {len(keep)} listed ({reused} curated kept, {created} new), {hidden} hidden, "
            f"{renamed} names made unique, {imaged} images matched, {with_image} of {len(keep)} have an image"
        ))

    def _donor(self, name, base, variant, donors):
        """Closest free-exercise-db row with the same movement and the same equipment, or None."""
        want = tokens(name)
        must = tokens(base)
        need = VARIANT_TOKENS.get(variant, set()) if variant else set()
        for v in need:
            want.discard(v)
        for alts in ([need] if need else []):
            want |= {sorted(alts)[0]}
        best, best_score = None, 0.0
        for have, row in donors:
            if not must <= have:
                continue
            if need and not need & have:
                continue
            if (have & EQUIPMENT_WORDS) - want - need:
                continue  # the donor uses other equipment
            score = len(want & have | (need & have)) / len(want | have)
            if score > best_score:
                best, best_score = row, score
        return best if best_score >= 0.6 else None

    def _unique_titles(self, ids) -> int:
        seen, changed = set(), 0
        rows = sorted(ExerciseTemplate.objects.filter(id__in=ids), key=lambda r: (r.source != "curated", len(r.title_en)))
        for r in rows:
            if r.title_fa in seen:
                r.title_fa = f"{r.title_fa} ({r.title_en})"
                r.save(update_fields=["title_fa", "search_text"])
                changed += 1
            seen.add(r.title_fa)
        return changed
