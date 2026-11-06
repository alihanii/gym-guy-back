"""Muscle-volume engine.

Every working set adds 1.0 to the exercise's primary muscle and 0.5 to each
secondary muscle. Warm-up sets are ignored. The same function scores a
coach's planned program and an athlete's logged workout, so the two
heatmaps are directly comparable.
"""
from collections import defaultdict
from typing import Iterable

from .models import ExerciseTemplate
from .taxonomy import PRIMARY_WEIGHT, SECONDARY_WEIGHT, Muscle, SetType


def _muscle_map(slugs: Iterable[str]) -> dict[str, tuple[str, list[str]]]:
    rows = ExerciseTemplate.objects.filter(slug__in=set(slugs)).values_list(
        "slug", "primary_muscle", "secondary_muscles"
    )
    return {slug: (primary, secondary) for slug, primary, secondary in rows}


def _working_sets(exercise: dict, only_done: bool) -> int:
    count = 0
    for s in exercise.get("sets", []):
        if s.get("type", SetType.NORMAL) == SetType.WARMUP:
            continue
        if only_done and not s.get("done"):
            continue
        count += 1
    return count


def compute_heatmap(exercise_lists: Iterable[list[dict]], only_done: bool = False) -> dict[str, float]:
    """Sum muscle volume over one or more lists of exercise blocks."""
    exercise_lists = list(exercise_lists)
    slugs = [ex.get("exercise_id") for lst in exercise_lists for ex in lst]
    lookup = _muscle_map(s for s in slugs if s)
    totals: dict[str, float] = defaultdict(float)
    for lst in exercise_lists:
        for ex in lst:
            info = lookup.get(ex.get("exercise_id"))
            if not info:
                continue
            n = _working_sets(ex, only_done)
            if not n:
                continue
            primary, secondary = info
            totals[primary] += PRIMARY_WEIGHT * n
            for m in secondary:
                totals[m] += SECONDARY_WEIGHT * n
    return {m: round(totals.get(m, 0.0), 2) for m in Muscle.values}
