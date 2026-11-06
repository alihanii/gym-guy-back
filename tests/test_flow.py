from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient


def auth(client: APIClient, phone, name, role):
    r = client.post("/api/auth/register/", {"phone": phone, "name": name, "password": "secret12", "role": role}, format="json")
    assert r.status_code == 201, r.data
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    return r.data["user"]


DAY = {
    "title": "روز اول - سینه و پشت بازو",
    "exercises": [
        {"exercise_id": "bench_press_barbell", "sets": [{"type": "warmup", "reps": "12"}] + [{"reps": "8-12"}] * 3, "tempo": "3-1-1-0", "target_rpe": 8},
        {"exercise_id": "cable_crossover", "superset_group": 1, "sets": [{"reps": "12"}] * 3},
        {"exercise_id": "push_up", "superset_group": 1, "sets": [{"reps": "AMRAP"}] * 3},
    ],
}


class CoreFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_exercises", verbosity=0)

    def setUp(self):
        self.coach, self.athlete = APIClient(), APIClient()
        auth(self.coach, "09120000001", "مربی تست", "coach")
        self.athlete_user = auth(self.athlete, "۰۹۱۲۰۰۰۰۰۰۲", "شاگرد تست", "athlete")

    def test_phone_is_normalised(self):
        self.assertEqual(self.athlete_user["phone"], "09120000002")

    def test_alias_search(self):
        r = self.athlete.get("/api/exercises/", {"q": "زیربغل قایقی"})
        self.assertEqual(r.data[0]["slug"], "seated_cable_row")
        r = self.athlete.get("/api/exercises/", {"q": "لت دست باز"})
        self.assertIn("lat_pulldown_cable", [e["slug"] for e in r.data])
        r = self.athlete.get("/api/exercises/", {"q": "جلوبازو لاري"})  # Arabic yeh
        self.assertIn("preacher_curl", [e["slug"] for e in r.data])

    def test_athlete_cannot_open_coach_portal(self):
        self.assertEqual(self.athlete.get("/api/coach/clients/").status_code, 403)

    def test_invite_flow_injects_routines_and_syncs_edits(self):
        client = self.coach.post("/api/coach/clients/", {"name": "علی", "injury_tags": ["shoulder"], "goal": "hypertrophy"}, format="json").data
        prog = self.coach.post("/api/coach/programs/", {"title": "هایپرتروفی ۸ هفته", "client": client["id"], "workouts": {"days": [DAY]}}, format="json")
        self.assertEqual(prog.status_code, 201, prog.data)
        prog = prog.data
        # heatmap: 3 working bench sets -> chest 3, + 3 crossover + 3 push-up = 9 chest
        self.assertEqual(prog["planned_heatmap"]["chest"], 9.0)
        self.assertEqual(prog["planned_heatmap"]["triceps"], 3.0)  # bench .5*3 + push-up .5*3
        # bench press is flagged for shoulder injury
        self.assertIn("bench_press_barbell", [c["exercise_id"] for c in prog["injury_conflicts"]])

        pub = self.coach.post(f"/api/coach/programs/{prog['id']}/publish/").data
        code = pub["invite_code"]
        self.assertRegex(code, r"^\d{6}$")
        self.assertTrue(pub["invite_link"].endswith(f"/join/{code}"))

        preview = self.athlete.get(f"/api/invites/{code}/").data
        self.assertEqual(preview["coach_name"], "مربی تست")
        fa_code = code.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
        r = self.athlete.post(f"/api/invites/FIT-{fa_code}/")
        self.assertEqual(r.status_code, 200, r.data)
        routines = self.athlete.get("/api/routines/").data
        self.assertEqual(len(routines), 1)
        self.assertEqual(routines[0]["coach_name"], "مربی تست")

        # coach edits the program -> athlete's routines follow
        days = [DAY, {"title": "روز دوم - پا", "exercises": [{"exercise_id": "squat_barbell", "sets": [{"reps": "5"}] * 5}]}]
        self.coach.patch(f"/api/coach/programs/{prog['id']}/", {"workouts": {"days": days}}, format="json")
        self.assertEqual([r["title"] for r in self.athlete.get("/api/routines/").data], [DAY["title"], "روز دوم - پا"])

        # a second athlete cannot reuse the code
        other = APIClient()
        auth(other, "09120000003", "نفر سوم", "athlete")
        self.assertEqual(other.post(f"/api/invites/{code}/").status_code, 409)

        # athlete logs a workout from the routine; coach sees it in monitoring
        rid = routines[0]["id"]
        w = self.athlete.post("/api/workouts/", {
            "title": DAY["title"], "routine": rid, "started_at": "2026-11-06T08:00:00Z", "duration_seconds": 3600,
            "exercises": [{"exercise_id": "bench_press_barbell", "sets": [
                {"type": "warmup", "weight_kg": 40, "reps": 12, "done": True},
                {"weight_kg": 80, "reps": 8, "done": True},
                {"weight_kg": 80, "reps": 7, "done": False},
            ]}],
        }, format="json")
        self.assertEqual(w.status_code, 201, w.data)
        self.assertEqual(w.data["total_sets"], 1)
        self.assertEqual(w.data["total_volume_kg"], 640)
        mon = self.coach.get(f"/api/coach/clients/{client['id']}/monitor/").data
        self.assertEqual(mon["sessions_this_week"], 1)
        self.assertEqual(mon["actual_heatmap"]["chest"], 1.0)
        self.assertEqual(mon["compliance"], 50)

    def test_records_and_previous_sets(self):
        def log(weight, reps):
            return self.athlete.post("/api/workouts/", {
                "title": "آزاد", "started_at": "2026-11-06T08:00:00Z", "duration_seconds": 1200,
                "exercises": [{"exercise_id": "squat_barbell", "sets": [{"weight_kg": weight, "reps": reps, "done": True}]}],
            }, format="json").data

        first = log(100, 5)
        self.assertEqual(first["records"], [])  # baseline only
        second = log(110, 5)
        kinds = {r["kind"] for r in second["records"]}
        self.assertEqual(kinds, {"est_1rm", "max_weight", "max_volume"})
        prev = self.athlete.get("/api/workouts/previous/", {"exercise_ids": "squat_barbell"}).data
        self.assertEqual(prev["squat_barbell"][0]["weight_kg"], 110)
        stats = self.athlete.get("/api/workouts/stats/").data
        self.assertEqual(stats["total_workouts"], 2)


class RoutineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_exercises", verbosity=0)

    def test_own_routine_crud_and_duplicate(self):
        c = APIClient()
        auth(c, "09120000009", "شاگرد", "athlete")
        body = {"title": "پا", "folder": "حجمی", "exercises": [{"exercise_id": "squat_barbell", "sets": [{"reps": "5"}] * 3}]}
        r = c.post("/api/routines/", body, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["folder"], "حجمی")
        rid = r.data["id"]
        self.assertEqual(c.patch(f"/api/routines/{rid}/", {"title": "پا سنگین"}, format="json").status_code, 200)
        dup = c.post(f"/api/routines/{rid}/duplicate/")
        self.assertEqual(dup.status_code, 201)
        self.assertEqual(dup.data["title"], "پا سنگین (کپی)")
        self.assertEqual(c.delete(f"/api/routines/{rid}/").status_code, 204)


class EditWorkoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_exercises", verbosity=0)

    def test_edit_recomputes_totals(self):
        c = APIClient()
        auth(c, "09120000010", "شاگرد", "athlete")
        w = c.post("/api/workouts/", {
            "title": "پا", "started_at": "2026-11-06T08:00:00Z", "duration_seconds": 1800,
            "exercises": [{"exercise_id": "squat_barbell", "sets": [{"weight_kg": 100, "reps": 5, "done": True}]}],
        }, format="json").data
        r = c.patch(f"/api/workouts/{w['id']}/", {
            "title": "پا سنگین",
            "exercises": [{"exercise_id": "squat_barbell", "sets": [{"weight_kg": 100, "reps": 5}, {"weight_kg": 110, "reps": 3}]}],
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["title"], "پا سنگین")
        self.assertEqual(r.data["total_sets"], 2)
        self.assertEqual(r.data["total_volume_kg"], 830)


class MeasurementAndStatsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_exercises", verbosity=0)

    def test_measurements_and_stats_shape(self):
        c = APIClient()
        auth(c, "09120000011", "شاگرد", "athlete")
        self.assertEqual(c.post("/api/measurements/", {}, format="json").status_code, 400)
        r = c.post("/api/measurements/", {"date": "2026-11-01", "weight_kg": 82.5, "waist_cm": 88}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(len(c.get("/api/measurements/").data), 1)
        c.post("/api/workouts/", {
            "title": "پا", "started_at": "2026-11-06T08:00:00Z", "duration_seconds": 1800,
            "exercises": [{"exercise_id": "squat_barbell", "sets": [{"weight_kg": 100, "reps": 5, "done": True}]}],
        }, format="json")
        s = c.get("/api/workouts/stats/").data
        self.assertIn("2026-11-06", s["days"])
        self.assertEqual(s["muscles_30d"]["quadriceps"], 1.0)
        self.assertEqual(s["weekly"][-1]["sets"], 1)
        self.assertEqual(s["weekly"][-1]["minutes"], 30)


class SocialTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_exercises", verbosity=0)

    def test_follow_feed_like_comment_and_privacy(self):
        a, b = APIClient(), APIClient()
        ua = auth(a, "09120000021", "آرش", "athlete")
        ub = auth(b, "09120000022", "بهار", "athlete")
        w = b.post("/api/workouts/", {
            "title": "پا", "started_at": "2026-11-06T08:00:00Z", "duration_seconds": 1800,
            "exercises": [{"exercise_id": "squat_barbell", "sets": [{"weight_kg": 100, "reps": 5, "done": True}]}],
        }, format="json").data
        self.assertEqual(a.get("/api/feed/").data["results"], [])
        self.assertEqual(len(a.get("/api/feed/discover/").data["results"]), 1)
        found = a.get("/api/users/", {"q": "بهار"}).data
        self.assertEqual(found[0]["id"], ub["id"])
        self.assertNotIn("phone", found[0])
        self.assertEqual(a.post(f"/api/users/{ub['id']}/follow/").status_code, 204)
        feed = a.get("/api/feed/").data["results"]
        self.assertEqual(feed[0]["id"], w["id"])
        self.assertEqual(feed[0]["exercises"][0]["best"]["weight_kg"], 100)
        self.assertEqual(a.post(f"/api/social/workouts/{w['id']}/like/").data["like_count"], 1)
        c = a.post(f"/api/social/workouts/{w['id']}/comments/", {"text": "عالی"}, format="json")
        self.assertEqual(c.status_code, 201)
        card = a.get("/api/feed/").data["results"][0]
        self.assertTrue(card["liked"])
        self.assertEqual(card["comment_count"], 1)
        # owner can delete others' comments on their workout
        self.assertEqual(b.delete(f"/api/social/comments/{c.data['id']}/").status_code, 204)
        # going private hides the workout
        b.patch("/api/auth/me/", {"is_private": True}, format="json")
        self.assertEqual(a.get("/api/feed/").data["results"], [])
        self.assertEqual(a.get(f"/api/social/workouts/{w['id']}/").status_code, 404)
        self.assertEqual(a.get(f"/api/users/{ub['id']}/").data["recent"], [])
        self.assertEqual(a.post(f"/api/users/{ua['id']}/follow/").status_code, 400)
