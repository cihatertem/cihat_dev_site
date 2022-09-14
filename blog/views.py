from django.db.models import Q
from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import parsers
from .paginations import CommentPagination, PostPagination
from .models import Post, Comment, Category, Tag
from .serializers import PostSerializer, CommentSerializer, CategorySerializer, TagSerializer


# Create your views here.
class PermissionMixin:
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class BlogApiViewSet(PermissionMixin, viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    pagination_class = PostPagination
    parser_classes = (parsers.MultiPartParser,
                      parsers.FormParser,
                      parsers.JSONParser)

    def perform_create(self, serializer: PostSerializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        queryset = Post.objects.all()
        search_key: str = self.request.query_params.get('search')
        if search_key is not None:
            search_key = search_key.strip(" ")
            queryset = queryset.filter(
                    Q(title__icontains=search_key) |
                    Q(ingredients__icontains=search_key) |
                    Q(slug__icontains=search_key)
            )
        return queryset


class CommentApiViewSet(PermissionMixin, viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class CategoryApiViewSet(PermissionMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = Category.objects.all()
        search_key: str = self.request.query_params.get('search')
        if search_key is not None:
            search_key = search_key.strip(" ")
            queryset = queryset.filter(name__icontains=search_key)
        return queryset


class TagApiViewSet(PermissionMixin, viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
