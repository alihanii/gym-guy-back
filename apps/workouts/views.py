from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncWeek
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import PersonalRecord, Routine, WorkoutLog
from apps.exercises.heatmap import compute_heatmap

from .records import estimate_1rm
from .serializers import PersonalRecordSerializer, RoutineSerializer, WorkoutSerializer


class RoutineViewSet(viewsets.ModelViewSet):
    serializer_class = RoutineSerializer

    def get_queryset(self):
        return Routine.objects.filter(owner=self.request.user).select_related("program__coach")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.program_id:
            raise PermissionDenied("روتین‌های برنامه مربی فقط توسط مربی تغییر می‌کنند؛ یک کپی بسازید.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.program_id:
            raise PermissionDenied("روتین‌های برنامه مربی را نمی‌توان حذف کرد.")
        instance.delete()

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        src = self.get_object()
        copy = Routine.objects.create(
            owner=request.user, title=f"{src.title} (کپی)", folder=src.folder, exercises=src.exercises
        )
        return Response(RoutineSerializer(copy, context={"request": request}).data, status=201)


class WorkoutViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                     mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = WorkoutSerializer

    def get_queryset(self):
        return WorkoutLog.objects.filter(user=self.request.user)

    @action(detail=False)
    def previous(self, request):
        """Last performed working sets for each requested exercise (the grey 'previous' column)."""
        ids = [i for i in request.query_params.get("exercise_ids", "").split(",") if i]
        out = {}
        for ex in ids[:40]:
            # JSON text match works on both SQLite and Postgres
            log = self.get_queryset().filter(exercise_ids__icontains=f'"{ex}"').order_by("-completed_at").first()
            if not log:
                continue
            for b in log.exercises:
                if b["exercise_id"] == ex:
                    out[ex] = [
                        {k: s.get(k) for k in ("type", "weight_kg", "reps", "duration_s", "distance_m")}
                        for s in b["sets"]
                    ]
                    break
        return Response(out)

    @action(detail=False)
    def exercise(self, request):
        """One exercise's history for the detail page: per-session best set, est. 1RM and volume, plus PRs."""
        ex = request.query_params.get("id", "")
        sessions = []
        logs = self.get_queryset().filter(exercise_ids__icontains=f'"{ex}"').order_by("-completed_at")[:100]
        for log in logs:
            sets = [s for b in log.exercises if b["exercise_id"] == ex for s in b["sets"] if s.get("done")]
            if not sets:
                continue
            working = [s for s in sets if s.get("type") != "warmup"]
            def one_rm(s):
                return estimate_1rm(s.get("weight_kg") or 0, s.get("reps") or 0)
            best = max(working, key=lambda s: (one_rm(s), s.get("reps") or 0), default=None)
            sessions.append({
                "workout_id": log.id,
                "title": log.title,
                "date": log.started_at.isoformat(),
                "sets": [{k: s.get(k) for k in ("type", "weight_kg", "reps", "duration_s", "distance_m", "rpe")} for s in sets],
                "best_set": {"weight_kg": best.get("weight_kg"), "reps": best.get("reps")} if best else None,
                "est_1rm": max((one_rm(s) for s in working), default=0),
                "max_weight": max(((s.get("weight_kg") or 0) for s in working), default=0),
                "max_reps": max(((s.get("reps") or 0) for s in working), default=0),
                "volume": round(sum((s.get("weight_kg") or 0) * (s.get("reps") or 0) for s in working), 1),
            })
        records = PersonalRecordSerializer(
            PersonalRecord.objects.filter(user=request.user, exercise_id=ex), many=True
        ).data
        return Response({"sessions": sessions, "records": records})

    @action(detail=False)
    def stats(self, request):
        qs = self.get_queryset()
        since = timezone.now() - timedelta(weeks=12)
        weekly = (
            qs.filter(completed_at__gte=since)
            .annotate(week=TruncWeek("completed_at"))
            .values("week")
            .annotate(volume=Sum("total_volume_kg"), sessions=Count("id"))
            .order_by("week")
        )
        # Streak: consecutive weeks (ending this or last week) with at least one workout.
        streak, cursor = 0, (timezone.localdate() - timedelta(days=timezone.localdate().weekday()))
        all_weeks = set(qs.annotate(week=TruncWeek("completed_at")).values_list("week", flat=True))
        all_weeks = {w.date() for w in all_weeks}
        if cursor not in all_weeks:
            cursor -= timedelta(weeks=1)
        while cursor in all_weeks:
            streak += 1
            cursor -= timedelta(weeks=1)
        recent = list(qs.filter(completed_at__gte=timezone.now() - timedelta(days=30)).values_list("exercises", flat=True))
        weekly_more = {
            w["week"]: w for w in qs.filter(completed_at__gte=since).annotate(week=TruncWeek("completed_at"))
            .values("week").annotate(minutes=Sum("duration_seconds"), sets=Sum("total_sets"))
        }
        days = sorted({
            timezone.localtime(d).date().isoformat()
            for d in qs.filter(started_at__gte=timezone.now() - timedelta(days=400)).values_list("started_at", flat=True)
        })
        return Response({
            "total_workouts": qs.count(),
            "days": days,
            "muscles_30d": compute_heatmap(recent, only_done=True),
            "streak_weeks": streak,
            "weekly": [
                {
                    "week": w["week"].date().isoformat(), "volume_kg": round(w["volume"] or 0), "sessions": w["sessions"],
                    "minutes": round((weekly_more[w["week"]]["minutes"] or 0) / 60),
                    "sets": weekly_more[w["week"]]["sets"] or 0,
                }
                for w in weekly
            ],
            "records": PersonalRecordSerializer(
                PersonalRecord.objects.filter(user=request.user).order_by("-achieved_at")[:20], many=True
            ).data,
        })
