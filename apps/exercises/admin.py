from django.contrib import admin

from .models import ExerciseTemplate


@admin.register(ExerciseTemplate)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ["title_fa", "title_en", "equipment", "primary_muscle", "is_custom"]
    list_filter = ["equipment", "primary_muscle", "is_custom"]
    search_fields = ["title_fa", "title_en", "search_text"]
