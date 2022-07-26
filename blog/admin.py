from django.contrib import admin
from .models import Post, Comment, Category, Tag

# Register your models here.
admin.site.register(Comment)
admin.site.register(Category)
admin.site.register(Tag)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title'[:200],)}
    ordering = ("-created_at",)
    list_display = ("title", "owner", "created_at", "updated_at")
    list_display_links = ("title",)
    list_filter = ('created_at', 'updated_at', "owner")
    search_fields = ('title',)
    list_per_page = 25
