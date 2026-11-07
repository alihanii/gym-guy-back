from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.exercises.heatmap import compute_heatmap
from apps.workouts.models import WorkoutLog
from apps.workouts.serializers import WorkoutSerializer

from .models import Client, Program, ProgramStatus, generate_invite_code
from .serializers import ClientSerializer, ProgramSerializer
from .services import planned_heatmap, redeem, sync_routines


class IsCoach(permissions.BasePermission):
    message = "این بخش مخصوص مربی‌هاست."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_coach)


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [IsCoach]

    def get_queryset(self):
        return Client.objects.filter(coach=self.request.user).select_related("athlete").prefetch_related("programs")

    def perform_create(self, serializer):
        serializer.save(coach=self.request.user)

    def perform_destroy(self, client):
        """Removing a student ends coaching: their programs are archived and leave the athlete's routines.
        Workouts the athlete already logged stay theirs."""
        for program in client.programs.all():
            program.routines.all().delete()
            program.status = ProgramStatus.ARCHIVED
            program.invite_code = None
            program.save(update_fields=["status", "invite_code"])
        client.delete()

    @action(detail=True)
    def monitor(self, request, pk=None):
        """Planned vs actual muscle volume for the last 7 days, compliance and recent logs."""
        client = self.get_object()
        program = client.programs.filter(status=ProgramStatus.ACTIVE).first()
        if not client.athlete_id or not program:
            return Response({"linked": bool(client.athlete_id), "program": None, "workouts": []})
        since = timezone.now() - timedelta(days=7)
        logs = WorkoutLog.objects.filter(user_id=client.athlete_id, program=program).order_by("-completed_at")
        week_logs = [l for l in logs if l.completed_at >= since]
        planned_days = max(len(program.days), 1)
        return Response({
            "linked": True,
            "program": {"id": program.id, "title": program.title},
            "planned_heatmap": program.planned_heatmap,
            "actual_heatmap": compute_heatmap([l.exercises for l in week_logs], only_done=True),
            "compliance": min(100, round(100 * len(week_logs) / planned_days)),
            "sessions_this_week": len(week_logs),
            "planned_sessions": planned_days,
            "workouts": WorkoutSerializer(logs[:10], many=True, context={"request": request}).data,
        })

    @action(detail=True, methods=["post"], url_path=r"workouts/(?P<workout_id>\d+)/feedback")
    def feedback(self, request, pk=None, workout_id=None):
        client = self.get_object()
        log = get_object_or_404(WorkoutLog, pk=workout_id, user_id=client.athlete_id)
        log.coach_feedback = (request.data.get("text") or "").strip()[:2000]
        log.save(update_fields=["coach_feedback"])
        return Response({"coach_feedback": log.coach_feedback})


class ProgramViewSet(viewsets.ModelViewSet):
    serializer_class = ProgramSerializer
    permission_classes = [IsCoach]

    def get_queryset(self):
        qs = Program.objects.filter(coach=self.request.user).select_related("client", "athlete")
        if client := self.request.query_params.get("client"):
            qs = qs.filter(client_id=client)
        return qs

    def _save(self, serializer, **extra):
        program = serializer.save(**extra)
        if program.client_id and not program.injury_tags and "injury_tags" not in serializer.initial_data:
            program.injury_tags = program.client.injury_tags
        program.planned_heatmap = planned_heatmap(program)
        program.save(update_fields=["planned_heatmap", "injury_tags"])
        sync_routines(program)  # live edit: athlete's routines follow the coach instantly

    def perform_create(self, serializer):
        self._save(serializer, coach=self.request.user)

    def perform_update(self, serializer):
        self._save(serializer)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        program = self.get_object()
        if not any(d.get("exercises") for d in program.days):
            return Response({"detail": "برنامه حداقل یک روز با حرکت لازم دارد."}, status=status.HTTP_400_BAD_REQUEST)
        if not program.invite_code:
            program.invite_code = generate_invite_code()
        if program.status == ProgramStatus.DRAFT:
            program.status = ProgramStatus.PENDING_INVITE
        program.save(update_fields=["invite_code", "status", "updated_at"])
        return Response(self.get_serializer(program).data)

    @action(detail=True, methods=["post"], url_path="new-code")
    def new_code(self, request, pk=None):
        program = self.get_object()
        program.invite_code = generate_invite_code()
        program.save(update_fields=["invite_code"])
        return Response(self.get_serializer(program).data)


def _clean_code(raw: str) -> str:
    digits = "".join(ch for ch in (raw or "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")) if ch.isdigit())
    return digits[-6:] if len(digits) >= 6 else digits


class InviteView(APIView):
    """GET previews an invite; POST links the current athlete to it."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "invite_redeem"

    def _program(self, code):
        code = _clean_code(code)
        return get_object_or_404(
            Program.objects.select_related("coach"),
            invite_code=code, status__in=[ProgramStatus.PENDING_INVITE, ProgramStatus.ACTIVE],
        )

    def get(self, request, code):
        p = self._program(code)
        return Response({
            "title": p.title, "coach_name": p.coach.name, "days": [d.get("title") for d in p.days],
            "already_linked": p.athlete_id == request.user.id,
        })

    def post(self, request, code):
        p = self._program(code)
        if p.athlete_id and p.athlete_id != request.user.id:
            return Response({"detail": "این کد قبلاً توسط شاگرد دیگری استفاده شده است."}, status=status.HTTP_409_CONFLICT)
        if p.coach_id == request.user.id:
            return Response({"detail": "نمی‌توانید کد برنامه خودتان را وارد کنید."}, status=status.HTTP_400_BAD_REQUEST)
        redeem(p, request.user)
        return Response({"program_id": p.id, "title": p.title, "coach_name": p.coach.name, "routines": len(p.days)})


class MyCoachesView(APIView):
    def get(self, request):
        programs = Program.objects.filter(athlete=request.user, status=ProgramStatus.ACTIVE).select_related("coach")
        return Response([
            {"program_id": p.id, "title": p.title, "coach_name": p.coach.name, "days": len(p.days)}
            for p in programs
        ])
