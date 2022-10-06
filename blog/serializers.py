from rest_framework import serializers
from .models import Post, Comment, Category, Tag


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    posts = serializers.HyperlinkedRelatedField(many=True,
                                                read_only=True,
                                                view_name='api:blog:post-detail')

    class Meta:
        model = Category
        fields = ('id', 'name', 'posts')
        read_only_fields = ('id', 'posts')


class PostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')
        read_only_fields = ('id',)


class PostSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')
    slug = serializers.ReadOnlyField()
    comments = serializers.HyperlinkedRelatedField(many=True,
                                                   read_only=True,
                                                   required=False,
                                                   view_name='api:blog:comment-detail')
    tags = TagSerializer(many=True, required=False)
    category = PostCategorySerializer(required=False)
    hero_img = serializers.ImageField(required=False)

    # comments = CommentSerializer(many=True, required=False)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        category = validated_data.pop('category', {})
        post = Post.objects.create(**validated_data)

        self._get_or_create_tags(tags, post)
        self._get_or_create_category(category, post)
        
        return post

    def update(self, instance: Post, validated_data):
        tags = validated_data.pop('tags', None)
        category: Category | None = validated_data.pop('category', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if category is not None:
            self._get_or_create_category(category, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def _get_or_create_tags(self, tags: Tag, post: Post) -> None:
        for tag in tags:
            tag_object, created = Tag.objects.get_or_create(**tag)
            post.tags.add(tag_object)

    def _get_or_create_category(self, category: Category, post: Post) -> None:
        category_obj, created = Category.objects.get_or_create(**category)
        category_obj.posts.add(post)
        post.category = category_obj

    class Meta:
        model = Post
        fields = ('id', 'owner', 'title', 'body', 'slug', 'created_at',
                  'updated_at', 'youtube_link', 'ingredients',
                  'time', 'difficulty', 'comments', 'category', 'tags',
                  'hero_img', "draft")
        read_only_fields = ('id', 'created_at', 'updated_at', 'comments')
