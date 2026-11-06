"""Import free-exercise-db (public domain) into the exercise bank.

    git clone --depth 1 https://github.com/yuhonas/free-exercise-db.git /tmp/fedb
    python manage.py import_free_exercise_db /tmp/fedb --images

Images are resized to WebP and saved through the default storage, so they
land on S3 when USE_S3=true. Re-running is safe: rows are matched by slug
and images that already exist are skipped unless --force-images.
"""
import io
import json
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from PIL import Image

from apps.exercises import fedb
from apps.exercises.models import ExerciseTemplate
from apps.exercises.taxonomy import Muscle


def to_webp(path: Path, width: int) -> ContentFile:
    im = Image.open(path).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=78, method=5)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = "Import or update exercises (with Persian titles and images) from a free-exercise-db checkout."

    def add_arguments(self, parser):
        parser.add_argument("path", help="free-exercise-db checkout (folder with dist/ and exercises/)")
        parser.add_argument("--images", action="store_true", help="upload start/end images")
        parser.add_argument("--force-images", action="store_true")
        parser.add_argument("--width", type=int, default=480)
        parser.add_argument("--skip-stretching", action="store_true")

    def handle(self, path, images, force_images, width, skip_stretching, **_):
        root = Path(path)
        data_file = root / "dist" / "exercises.json"
        if not data_file.exists():
            raise CommandError(f"{data_file} not found")
        rows = json.loads(data_file.read_text())
        created = updated = merged = uploaded = 0
        for ex in rows:
            if skip_stretching and ex.get("category") == "stretching":
                continue
            curated_slug = fedb.CURATED.get(ex["name"])
            primary = next((fedb.MUSCLE_MAP[m] for m in ex["primaryMuscles"] if m in fedb.MUSCLE_MAP), None)
            if ex.get("category") == "cardio":
                primary = Muscle.CARDIO
            if primary is None:
                continue
            equipment = fedb.EQUIPMENT_MAP.get(ex.get("equipment"), fedb.EQUIPMENT_MAP[None])
            if ex.get("category") == "stretching":
                equipment = fedb.EQUIPMENT_MAP[None] if ex.get("equipment") in (None, "other", "foam roll") else equipment
            extra = {
                "instructions": ex.get("instructions", []),
                "level": ex.get("level") or "",
                "category": ex.get("category") or "",
            }
            if curated_slug and (obj := ExerciseTemplate.objects.filter(slug=curated_slug).first()):
                for k, v in extra.items():
                    setattr(obj, k, v)
                if ex["name"] not in obj.persian_aliases and ex["name"] != obj.title_en:
                    obj.persian_aliases = [*obj.persian_aliases, ex["name"]]
                merged += 1
            else:
                title_fa, _ = fedb.persian_title(ex["name"])
                secondary = []
                for m in ex["secondaryMuscles"]:
                    mm = fedb.MUSCLE_MAP.get(m)
                    if mm and mm != primary and mm not in secondary:
                        secondary.append(mm)
                obj, was_created = ExerciseTemplate.objects.get_or_create(
                    slug=fedb.slug_for(ex["id"]),
                    defaults={"title_en": ex["name"], "title_fa": title_fa, "equipment": equipment, "primary_muscle": primary},
                )
                obj.title_en = ex["name"]
                obj.title_fa = title_fa
                obj.equipment = equipment
                obj.tracking_type = fedb.tracking_for(ex, equipment)
                obj.primary_muscle = primary
                obj.secondary_muscles = secondary
                obj.injury_warnings = fedb.injuries_for(ex["name"])
                obj.source = "free-exercise-db"
                for k, v in extra.items():
                    setattr(obj, k, v)
                created += was_created
                updated += not was_created

            if images:
                files = sorted((root / "exercises").joinpath(ex["id"]).glob("*.jpg"))
                for field, f in zip(("thumbnail", "image_end"), files[:2]):
                    if getattr(obj, field) and not force_images:
                        continue
                    getattr(obj, field).save(f"{obj.slug}_{field}.webp", to_webp(f, width), save=False)
                    uploaded += 1
            obj.save()
        renamed = self._disambiguate()
        self.stdout.write(self.style.SUCCESS(
            f"free-exercise-db: {renamed} names made unique, {created} new, {updated} updated, {merged} merged into curated, {uploaded} images uploaded"
        ))

    def _disambiguate(self) -> int:
        """Imported rows that share a Persian name get qualifiers; curated names never change."""
        from collections import defaultdict
        rows = list(ExerciseTemplate.objects.all())
        groups = defaultdict(list)
        for r in rows:
            groups[r.title_fa].append(r)
        taken = {r.title_fa for r in rows}
        changed = 0
        for title, members in groups.items():
            if len(members) < 2:
                continue
            imported = [m for m in members if m.source == "free-exercise-db"]
            # keep one plain name when no curated row already owns it: the shortest English name
            if len(imported) == len(members):
                imported.sort(key=lambda m: len(m.title_en))
                imported = imported[1:]
            for m in imported:
                new = fedb.disambiguate(title, m.title_en)
                if new == title or new in taken:
                    new = f"{new} ({m.title_en})"
                taken.add(new)
                m.title_fa = new
                m.save(update_fields=["title_fa", "search_text"])
                changed += 1
        return changed
