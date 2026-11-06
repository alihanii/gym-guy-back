import uuid

from django.db.models import Q
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import ExerciseTemplate
from .serializers import ExerciseSerializer
from .taxonomy import Equipment, InjuryTag, Muscle, TrackingType
from .text import match_score, normalize_fa


class IsOwnerOfCustom(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.is_custom and obj.created_by_id == request.user.id


class ExerciseViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
    mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet,
):
    """Exercise bank. Built-ins are read-only; users may add their own."""

    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOfCustom]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    lookup_field = "slug"

    def get_queryset(self):
        qs = ExerciseTemplate.objects.filter(Q(is_custom=False) | Q(created_by=self.request.user))
        p = self.request.query_params
        if q := normalize_fa(p.get("q", "")):
            for word in q.split():
                qs = qs.filter(search_text__icontains=word)
        if eq := p.get("equipment"):
            qs = qs.filter(equipment__in=eq.split(","))
        if m := p.get("muscle"):
            muscles = m.split(",")
            # JSON list lookups differ between SQLite and Postgres; filter the (small) bank in Python.
            ids = [e.id for e in qs if e.primary_muscle in muscles or set(e.secondary_muscles) & set(muscles)]
            qs = qs.filter(id__in=ids)
        return qs

    def list(self, request, *args, **kwargs):
        qs = list(self.get_queryset())
        if q := normalize_fa(request.query_params.get("q", "")):
            qs.sort(key=lambda e: -match_score(q, [e.title_fa, e.title_en, *e.persian_aliases]))
        return Response(self.get_serializer(qs, many=True).data)

    def perform_create(self, serializer):
        slug = serializer.validated_data.get("slug") or f"custom_{uuid.uuid4().hex[:10]}"
        serializer.save(slug=slug, is_custom=True, created_by=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def taxonomy(self, request):
        """Labels for every enum, so the frontend never hard-codes Persian strings twice."""
        def pairs(enum):
            return [{"value": v, "label": l} for v, l in enum.choices]

        return Response({
            "equipment": pairs(Equipment),
            "muscles": pairs(Muscle),
            "tracking_types": pairs(TrackingType),
            "injury_tags": pairs(InjuryTag),
        })
