from django.contrib import admin

from .models import Client, Program

admin.site.register(Client)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ["title", "coach", "athlete", "status", "invite_code", "updated_at"]
    list_filter = ["status"]
