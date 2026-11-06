"""Volume and personal-record detection for a finished workout."""
from apps.exercises.models import ExerciseTemplate
from apps.exercises.taxonomy import SetType, TrackingType

from .models import PersonalRecord, RecordKind

WEIGHTED = {TrackingType.WEIGHT_REPS, TrackingType.BODYWEIGHT_REPS}


def estimate_1rm(weight: float, reps: int) -> float:
    """Epley formula; a single is the 1RM itself."""
    if reps <= 0 or weight <= 0:
        return 0.0
    return weight if reps == 1 else round(weight * (1 + reps / 30), 1)


def _counted(s: dict) -> bool:
    return s.get("done") and s.get("type") != SetType.WARMUP


def summarize(blocks: list[dict]) -> tuple[float, int]:
    volume, sets = 0.0, 0
    for b in blocks:
        for s in b["sets"]:
            if not _counted(s):
                continue
            sets += 1
            volume += (s.get("weight_kg") or 0) * (s.get("reps") or 0)
    return round(volume, 1), sets


def detect_records(workout) -> list[dict]:
    """Compare each exercise's best working set with stored PRs; save and return new ones."""
    tracking = dict(
        ExerciseTemplate.objects.filter(slug__in=workout.exercise_ids).values_list("slug", "tracking_type")
    )
    best: dict[tuple[str, str], float] = {}
    for b in workout.exercises:
        ex = b["exercise_id"]
        kind_of = tracking.get(ex)
        for s in b["sets"]:
            if not _counted(s):
                continue
            w, r = s.get("weight_kg") or 0, s.get("reps") or 0
            candidates = {}
            if kind_of in WEIGHTED and w > 0 and r > 0:
                candidates = {
                    RecordKind.EST_1RM: estimate_1rm(w, r),
                    RecordKind.MAX_WEIGHT: w,
                    RecordKind.MAX_VOLUME: w * r,
                }
            elif kind_of in {TrackingType.REPS_ONLY, TrackingType.BODYWEIGHT_REPS} and r > 0:
                candidates = {RecordKind.MAX_REPS: r}
            for kind, value in candidates.items():
                key = (ex, kind)
                best[key] = max(best.get(key, 0), value)

    existing = {
        (p.exercise_id, p.kind): p
        for p in PersonalRecord.objects.filter(user=workout.user, exercise_id__in=workout.exercise_ids)
    }
    broken = []
    for (ex, kind), value in best.items():
        prev = existing.get((ex, kind))
        if prev and prev.value >= value:
            continue
        PersonalRecord.objects.update_or_create(
            user=workout.user, exercise_id=ex, kind=kind,
            defaults={"value": value, "workout": workout, "achieved_at": workout.completed_at},
        )
        if prev is None:
            continue  # first time logging this lift sets a baseline, not a celebration
        broken.append({
            "exercise_id": ex, "kind": kind, "value": round(value, 1),
            "previous": round(prev.value, 1),
        })
    return broken
