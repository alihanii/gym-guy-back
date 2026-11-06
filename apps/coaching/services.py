from django.db import transaction

from apps.exercises.heatmap import compute_heatmap
from apps.exercises.models import ExerciseTemplate
from apps.workouts.models import Routine

from .models import Program, ProgramStatus


def planned_heatmap(program: Program) -> dict[str, float]:
    return compute_heatmap([d.get("exercises", []) for d in program.days])


def injury_conflicts(days: list[dict], injury_tags: list[str]) -> list[dict]:
    """Exercises in the plan that are flagged for one of the client's injuries."""
    if not injury_tags:
        return []
    slugs = {b["exercise_id"] for d in days for b in d.get("exercises", [])}
    flagged = {
        slug: (title, [t for t in warnings if t in injury_tags])
        for slug, title, warnings in ExerciseTemplate.objects.filter(slug__in=slugs).values_list(
            "slug", "title_fa", "injury_warnings"
        )
        if set(warnings) & set(injury_tags)
    }
    out = []
    for di, d in enumerate(days):
        for bi, b in enumerate(d.get("exercises", [])):
            if b["exercise_id"] in flagged:
                title, tags = flagged[b["exercise_id"]]
                out.append({"day": di, "index": bi, "exercise_id": b["exercise_id"], "title_fa": title, "tags": tags})
    return out


@transaction.atomic
def sync_routines(program: Program) -> None:
    """Mirror the program's days into the linked athlete's routines (create/update/delete)."""
    if not program.athlete_id or program.status != ProgramStatus.ACTIVE:
        Routine.objects.filter(program=program).delete()
        return
    existing = {r.day_index: r for r in Routine.objects.filter(program=program)}
    for i, day in enumerate(program.days):
        r = existing.pop(i, None) or Routine(owner_id=program.athlete_id, program=program, day_index=i)
        r.owner_id = program.athlete_id
        r.title = day.get("title") or f"روز {i + 1}"
        r.exercises = day.get("exercises", [])
        r.save()
    for leftover in existing.values():
        leftover.delete()


@transaction.atomic
def redeem(program: Program, athlete) -> Program:
    # One active program per coach-athlete pair: archive the older ones.
    for old in Program.objects.filter(coach=program.coach, athlete=athlete, status=ProgramStatus.ACTIVE).exclude(pk=program.pk):
        old.status = ProgramStatus.ARCHIVED
        old.save(update_fields=["status"])
        sync_routines(old)
    program.athlete = athlete
    program.status = ProgramStatus.ACTIVE
    program.save(update_fields=["athlete", "status", "updated_at"])
    if program.client_id and not program.client.athlete_id:
        program.client.athlete = athlete
        program.client.save(update_fields=["athlete"])
    sync_routines(program)
    return program
