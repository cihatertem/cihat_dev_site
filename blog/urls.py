from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import BlogApiViewSet, CommentApiViewSet, CategoryApiViewSet, TagApiViewSet, SinglePostWithSlug

app_name = 'blog'
router = DefaultRouter(trailing_slash=False)
router.register(r"posts", BlogApiViewSet)
router.register(r"comments", CommentApiViewSet)
router.register(r"categories", CategoryApiViewSet)
router.register(r"tags", TagApiViewSet)

urlpatterns = [
    path("posts/slug/<str:slug>", SinglePostWithSlug.as_view(), name="post-with-slug")
]

urlpatterns += router.urls
