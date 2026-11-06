"""Public feed: follow people, see their workouts, like and comment. Phone numbers never leave this module."""
from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.workouts.models import WorkoutLog
from apps.workouts.records import estimate_1rm

from .models import Comment, Follow, Like

User = get_user_model()
PAGE = 20


def visible_workouts(me):
    return WorkoutLog.objects.filter(Q(user=me) | Q(user__is_private=False))


def public_user(u, me=None):
    return {"id": u.id, "name": u.name, "is_coach": u.is_coach, "is_me": bool(me and me.id == u.id)}


def card(w, me):
    """A feed card: totals plus each exercise's set count and best set."""
    exercises = []
    for b in w.exercises:
        working = [s for s in b["sets"] if s.get("type") != "warmup"] or b["sets"]
        best = max(working, key=lambda s: (estimate_1rm(s.get("weight_kg") or 0, s.get("reps") or 0), s.get("reps") or 0))
        exercises.append({
            "exercise_id": b["exercise_id"], "sets": len(b["sets"]),
            "best": {k: best.get(k) for k in ("weight_kg", "reps", "duration_s", "distance_m")},
        })
    return {
        "id": w.id, "title": w.title, "notes": w.notes, "started_at": w.started_at, "duration_seconds": w.duration_seconds,
        "total_volume_kg": w.total_volume_kg, "total_sets": w.total_sets, "records": len(w.records),
        "exercises": exercises, "user": public_user(w.user, me),
        "like_count": w.like_count, "liked": w.liked, "comment_count": w.comment_count,
    }


def annotate(qs, me):
    return qs.select_related("user").annotate(
        like_count=Count("likes", distinct=True),
        comment_count=Count("comments", distinct=True),
        liked=Exists(Like.objects.filter(workout=OuterRef("pk"), user=me)),
    )


def page(qs, request):
    before = request.query_params.get("before")
    if before and before.isdigit():
        qs = qs.filter(id__lt=int(before))
    items = list(qs.order_by("-id")[:PAGE])
    return items, (items[-1].id if len(items) == PAGE else None)


class FeedView(APIView):
    """Workouts from people I follow, plus my own."""

    def get(self, request):
        me = request.user
        following = Follow.objects.filter(follower=me).values("following")
        qs = annotate(visible_workouts(me).filter(Q(user=me) | Q(user__in=following)), me)
        items, nxt = page(qs, request)
        return Response({"results": [card(w, me) for w in items], "next": nxt})


class DiscoverView(APIView):
    """Recent public workouts from everyone, for an empty feed."""

    def get(self, request):
        me = request.user
        items, nxt = page(annotate(visible_workouts(me).exclude(user=me), me), request)
        return Response({"results": [card(w, me) for w in items], "next": nxt})


class UserSearchView(APIView):
    def get(self, request):
        q = request.query_params.get("q", "").strip()
        me = request.user
        qs = User.objects.exclude(id=me.id).filter(is_active=True)
        if q:
            qs = qs.filter(name__icontains=q)
        qs = qs.annotate(
            followers=Count("follower_rel", distinct=True),
            followed=Exists(Follow.objects.filter(follower=me, following=OuterRef("pk"))),
        ).order_by("-followers", "name")[:30]
        return Response([{**public_user(u, me), "followers": u.followers, "is_following": u.followed} for u in qs])


class UserProfileView(APIView):
    def get(self, request, pk):
        me = request.user
        u = get_object_or_404(User, pk=pk, is_active=True)
        hidden = u.is_private and u.id != me.id
        data = {
            **public_user(u, me),
            "is_private": u.is_private,
            "followers": Follow.objects.filter(following=u).count(),
            "following": Follow.objects.filter(follower=u).count(),
            "workouts": WorkoutLog.objects.filter(user=u).count(),
            "is_following": Follow.objects.filter(follower=me, following=u).exists(),
            "recent": [],
            "next": None,
        }
        if not hidden:
            items, nxt = page(annotate(WorkoutLog.objects.filter(user=u), me), request)
            data["recent"], data["next"] = [card(w, me) for w in items], nxt
        return Response(data)


class FollowView(APIView):
    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk, is_active=True)
        if target.id == request.user.id:
            return Response({"detail": "نمی‌توانید خودتان را دنبال کنید."}, status=400)
        Follow.objects.get_or_create(follower=request.user, following=target)
        return Response(status=204)

    def delete(self, request, pk):
        Follow.objects.filter(follower=request.user, following_id=pk).delete()
        return Response(status=204)


class SocialWorkoutView(APIView):
    """Full detail of someone's public workout."""

    def get(self, request, pk):
        from apps.workouts.serializers import WorkoutSerializer

        w = get_object_or_404(annotate(visible_workouts(request.user), request.user), pk=pk)
        data = WorkoutSerializer(w, context={"request": request}).data
        data.pop("coach_feedback", None)
        return Response({**data, **{k: card(w, request.user)[k] for k in ("user", "like_count", "liked", "comment_count")}})


class LikeView(APIView):
    def post(self, request, pk):
        w = get_object_or_404(visible_workouts(request.user), pk=pk)
        Like.objects.get_or_create(user=request.user, workout=w)
        return Response({"like_count": w.likes.count(), "liked": True})

    def delete(self, request, pk):
        w = get_object_or_404(visible_workouts(request.user), pk=pk)
        Like.objects.filter(user=request.user, workout=w).delete()
        return Response({"like_count": w.likes.count(), "liked": False})


class CommentSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=500, trim_whitespace=True)


def comment_json(c, me):
    return {"id": c.id, "text": c.text, "created_at": c.created_at, "user": public_user(c.user, me),
            "can_delete": c.user_id == me.id or c.workout.user_id == me.id}


class CommentsView(APIView):
    def get(self, request, pk):
        w = get_object_or_404(visible_workouts(request.user), pk=pk)
        return Response([comment_json(c, request.user) for c in w.comments.select_related("user", "workout")])

    def post(self, request, pk):
        w = get_object_or_404(visible_workouts(request.user), pk=pk)
        ser = CommentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        c = Comment.objects.create(user=request.user, workout=w, text=ser.validated_data["text"])
        return Response(comment_json(c, request.user), status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    def delete(self, request, pk):
        c = get_object_or_404(Comment.objects.select_related("workout"), pk=pk)
        if request.user.id not in (c.user_id, c.workout.user_id):
            return Response(status=403)
        c.delete()
        return Response(status=204)
