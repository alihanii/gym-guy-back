from rest_framework import serializers

from apps.workouts.schemas import TemplateBlockSerializer, validate_exercise_ids

from .models import Client, Program


class ProgramDaySerializer(serializers.Serializer):
    title = serializers.CharField(max_length=120, allow_blank=True, default="")
    exercises = TemplateBlockSerializer(many=True)


class WorkoutsSerializer(serializers.Serializer):
    days = ProgramDaySerializer(many=True)


class ProgramSerializer(serializers.ModelSerializer):
    workouts = WorkoutsSerializer()
    invite_link = serializers.CharField(read_only=True)
    client_name = serializers.CharField(source="client.name", read_only=True, default=None)
    athlete_name = serializers.CharField(source="athlete.name", read_only=True, default=None)
    injury_conflicts = serializers.SerializerMethodField()

    class Meta:
        model = Program
        fields = [
            "id", "title", "client", "client_name", "athlete_name", "status", "invite_code", "invite_link",
            "injury_tags", "workouts", "diet_plan", "planned_heatmap", "injury_conflicts",
            "start_date", "end_date", "created_at", "updated_at",
        ]
        read_only_fields = ["status", "invite_code", "planned_heatmap", "created_at", "updated_at"]

    def get_injury_conflicts(self, obj):
        from .services import injury_conflicts
        return injury_conflicts(obj.days, obj.injury_tags)

    def validate_client(self, client):
        if client and client.coach_id != self.context["request"].user.id:
            raise serializers.ValidationError("این شاگرد در لیست شما نیست.")
        return client

    def validate_workouts(self, value):
        blocks = [b for d in value["days"] for b in d["exercises"]]
        validate_exercise_ids(blocks, self.context["request"].user)
        return value


class ClientSerializer(serializers.ModelSerializer):
    athlete_name = serializers.CharField(source="athlete.name", read_only=True, default=None)
    active_program = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id", "name", "age", "height_cm", "weight_kg", "experience_months", "goal", "days_per_week",
            "injury_tags", "notes", "athlete", "athlete_name", "active_program", "created_at",
        ]
        read_only_fields = ["athlete", "created_at"]

    def get_active_program(self, obj):
        p = next((p for p in obj.programs.all() if p.status in ("active", "pending_invite", "draft")), None)
        return p and {"id": p.id, "title": p.title, "status": p.status, "invite_code": p.invite_code}
