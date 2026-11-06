"""Validation for the JSON blocks stored on routines, programs and workout logs."""
from rest_framework import serializers

from apps.exercises.models import ExerciseTemplate
from apps.exercises.taxonomy import SetType


class TemplateSetSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=SetType.values, default=SetType.NORMAL)
    reps = serializers.CharField(max_length=12, allow_blank=True, required=False, default="")  # "8-12"
    weight_kg = serializers.FloatField(required=False, allow_null=True, default=None)
    duration_s = serializers.IntegerField(required=False, allow_null=True, min_value=0, default=None)


class TemplateBlockSerializer(serializers.Serializer):
    exercise_id = serializers.CharField(max_length=80)
    superset_group = serializers.IntegerField(required=False, allow_null=True, default=None)
    rest_seconds = serializers.IntegerField(required=False, min_value=0, max_value=900, default=90)
    tempo = serializers.CharField(required=False, allow_blank=True, max_length=12, default="")
    target_rpe = serializers.FloatField(required=False, allow_null=True, min_value=1, max_value=10, default=None)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    sets = TemplateSetSerializer(many=True)


class PerformedSetSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=SetType.values, default=SetType.NORMAL)
    weight_kg = serializers.FloatField(required=False, allow_null=True, default=None)
    reps = serializers.IntegerField(required=False, allow_null=True, min_value=0, default=None)
    duration_s = serializers.IntegerField(required=False, allow_null=True, min_value=0, default=None)
    distance_m = serializers.FloatField(required=False, allow_null=True, min_value=0, default=None)
    rpe = serializers.FloatField(required=False, allow_null=True, min_value=1, max_value=10, default=None)
    done = serializers.BooleanField(default=False)


class PerformedBlockSerializer(serializers.Serializer):
    exercise_id = serializers.CharField(max_length=80)
    superset_group = serializers.IntegerField(required=False, allow_null=True, default=None)
    rest_seconds = serializers.IntegerField(required=False, min_value=0, max_value=900, default=90)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    sets = PerformedSetSerializer(many=True)


def validate_exercise_ids(blocks: list[dict], user) -> None:
    from django.db.models import Q

    ids = {b["exercise_id"] for b in blocks}
    known = set(
        ExerciseTemplate.objects.filter(slug__in=ids)
        .filter(Q(is_custom=False) | Q(created_by=user))
        .values_list("slug", flat=True)
    )
    missing = ids - known
    if missing:
        raise serializers.ValidationError(f"حرکت ناشناخته: {', '.join(sorted(missing))}")
