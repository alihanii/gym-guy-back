from django.db import transaction
from rest_framework import serializers

from apps.exercises.heatmap import compute_heatmap

from .models import PersonalRecord, Routine, WorkoutLog
from .records import detect_records, summarize
from .schemas import PerformedBlockSerializer, TemplateBlockSerializer, validate_exercise_ids


class RoutineSerializer(serializers.ModelSerializer):
    exercises = TemplateBlockSerializer(many=True)
    program_title = serializers.CharField(source="program.title", read_only=True, default=None)
    coach_name = serializers.CharField(source="program.coach.name", read_only=True, default=None)

    class Meta:
        model = Routine
        fields = ["id", "title", "folder", "exercises", "program", "program_title", "coach_name", "day_index", "updated_at"]
        read_only_fields = ["program", "day_index"]

    def validate_exercises(self, blocks):
        validate_exercise_ids(blocks, self.context["request"].user)
        return blocks


class WorkoutSerializer(serializers.ModelSerializer):
    exercises = PerformedBlockSerializer(many=True)

    class Meta:
        model = WorkoutLog
        fields = [
            "id", "title", "program", "routine", "started_at", "duration_seconds", "exercises",
            "actual_heatmap", "total_volume_kg", "total_sets", "records", "notes", "coach_feedback", "completed_at",
        ]
        read_only_fields = ["actual_heatmap", "total_volume_kg", "total_sets", "records", "coach_feedback", "completed_at"]

    def validate_exercises(self, blocks):
        if not blocks:
            raise serializers.ValidationError("تمرین بدون حرکت ذخیره نمی‌شود.")
        validate_exercise_ids(blocks, self.context["request"].user)
        return blocks

    def validate(self, attrs):
        user = self.context["request"].user
        if (r := attrs.get("routine")) and r.owner_id != user.id:
            raise serializers.ValidationError({"routine": "این روتین متعلق به شما نیست."})
        if (p := attrs.get("program")) and p.athlete_id != user.id:
            raise serializers.ValidationError({"program": "این برنامه به شما اختصاص داده نشده."})
        if attrs.get("routine") and not attrs.get("program"):
            attrs["program"] = attrs["routine"].program
        return attrs

    @transaction.atomic
    def create(self, validated):
        blocks = validated["exercises"]
        # Only finished sets are kept; empty blocks are dropped.
        for b in blocks:
            b["sets"] = [s for s in b["sets"] if s.get("done")]
        blocks = [b for b in blocks if b["sets"]]
        if not blocks:
            raise serializers.ValidationError({"exercises": "هیچ ستی تیک نخورده است."})
        validated["exercises"] = blocks
        validated["exercise_ids"] = sorted({b["exercise_id"] for b in blocks})
        validated["total_volume_kg"], validated["total_sets"] = summarize(blocks)
        validated["actual_heatmap"] = compute_heatmap([blocks], only_done=True)
        workout = WorkoutLog.objects.create(user=self.context["request"].user, **validated)
        workout.records = detect_records(workout)
        workout.save(update_fields=["records"])
        return workout


    @transaction.atomic
    def update(self, workout, validated):
        """Editing a past workout: title, notes, date, duration and its sets. Totals are recomputed; records stay as logged."""
        if "exercises" in validated:
            blocks = [b for b in validated["exercises"] if b["sets"]]
            for b in blocks:
                for st in b["sets"]:
                    st["done"] = True
            if not blocks:
                raise serializers.ValidationError({"exercises": "تمرین بدون ست ذخیره نمی‌شود."})
            validated["exercises"] = blocks
            validated["exercise_ids"] = sorted({b["exercise_id"] for b in blocks})
            validated["total_volume_kg"], validated["total_sets"] = summarize(blocks)
            validated["actual_heatmap"] = compute_heatmap([blocks], only_done=True)
        for k in ("routine", "program"):
            validated.pop(k, None)
        return super().update(workout, validated)


class PersonalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalRecord
        fields = ["exercise_id", "kind", "value", "achieved_at", "workout"]
