from django.contrib import admin
from .models import Skill, Work
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
admin.site.register(User, UserAdmin)


@admin.register(Work)
class WorksAdmin(admin.ModelAdmin):
    ordering = ["-created"]
    list_display = ["work_title", "address", "created"]


    class Meta:
        model = Work


@admin.register(Skill)
class SkillsAdmin(admin.ModelAdmin):
    ordering = ["-created"]
    list_display = ["skill", "created"]


    class Meta:
        model = Skill
