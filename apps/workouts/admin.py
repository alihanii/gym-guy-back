from django.contrib import admin

from .models import PersonalRecord, Routine, WorkoutLog

admin.site.register(Routine)
admin.site.register(PersonalRecord)


@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "total_volume_kg", "completed_at"]
