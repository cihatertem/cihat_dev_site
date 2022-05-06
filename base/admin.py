from django.contrib import admin
from .models import Skill, Work, SpamFilter
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
admin.site.register(User, UserAdmin)


@admin.register(Work)
class WorksAdmin(admin.ModelAdmin):
    __slot__ = "ordering", "list_display"
    ordering = ["-created"]
    list_display = ["work_title", "address", "created"]

    class Meta:
        __slot__ = "model"
        model = Work


@admin.register(Skill)
class SkillsAdmin(admin.ModelAdmin):
    __slot__ = "ordering", "list_display"
    ordering = ["-created"]
    list_display = ["skill", "created"]

    class Meta:
        __slot__ = "model"
        model = Skill


@admin.register(SpamFilter)
class SpamFilterAdmin(admin.ModelAdmin):
    __slot__ = "ordering", "list_display", "list_filter", "search_fields", "list_per_page"
    ordering = ("keyword",)
    list_display = ("keyword",)
    list_filter = ("keyword", 'created')
    search_fields = ('keyword',)
    list_per_page = 25
