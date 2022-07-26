from rest_framework import pagination


class PostPagination(pagination.PageNumberPagination):
    page_size = 8


class CommentPagination(pagination.PageNumberPagination):
    page_size = 2
