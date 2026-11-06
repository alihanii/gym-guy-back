from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.social import views as social
from apps.accounts.views import MeasurementViewSet, LoginView, MeView, RegisterView
from apps.coaching.views import ClientViewSet, InviteView, MyCoachesView, ProgramViewSet
from apps.exercises.views import ExerciseViewSet
from apps.workouts.views import RoutineViewSet, WorkoutViewSet

router = DefaultRouter()
router.register("exercises", ExerciseViewSet, basename="exercise")
router.register("routines", RoutineViewSet, basename="routine")
router.register("workouts", WorkoutViewSet, basename="workout")
router.register("measurements", MeasurementViewSet, basename="measurement")
router.register("coach/clients", ClientViewSet, basename="client")
router.register("coach/programs", ProgramViewSet, basename="program")

api = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("invites/<str:code>/", InviteView.as_view()),
    path("me/coaches/", MyCoachesView.as_view()),
    path("feed/", social.FeedView.as_view()),
    path("feed/discover/", social.DiscoverView.as_view()),
    path("users/", social.UserSearchView.as_view()),
    path("users/<int:pk>/", social.UserProfileView.as_view()),
    path("users/<int:pk>/follow/", social.FollowView.as_view()),
    path("social/workouts/<int:pk>/", social.SocialWorkoutView.as_view()),
    path("social/workouts/<int:pk>/like/", social.LikeView.as_view()),
    path("social/workouts/<int:pk>/comments/", social.CommentsView.as_view()),
    path("social/comments/<int:pk>/", social.CommentDeleteView.as_view()),
    path("", include(router.urls)),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api)),
]
if not getattr(settings, "USE_S3", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
