from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _
from base.utils import photo_resizer
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
import uuid


def post_directory_path(instance, filename) -> str:
    return 'posts/{0}/{1}'.format(instance.title, filename)


class Category(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        if self.name is not None:
            self.name = self.name.lower()
        super(Category, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ("name",)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Post(models.Model):
    CHOICES = (
        ("1", "Easy",), ("2", "Medium",), ("3", "Hard",)
    )

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=200, null=True, unique=True)
    short_description = models.CharField(max_length=350, null=True, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hero_img = models.ImageField(null=True,
                                 blank=True,
                                 default="default.jpg",
                                 upload_to=post_directory_path,
                                 verbose_name="Post's Hero Image")
    youtube_link = models.URLField(max_length=2000, null=True, blank=True)
    ingredients = models.TextField(help_text=_("Seperate ingredients with ','"),
                                   null=True, blank=True)
    time = models.DecimalField(max_digits=3, decimal_places=0, null=True, blank=True)
    difficulty = models.CharField(max_length=50, choices=CHOICES, null=True, blank=True)
    category = models.ForeignKey(Category,
                                 related_name="posts",
                                 on_delete=models.SET_NULL,
                                 null=True, blank=True)
    tags = models.ManyToManyField('Tag', related_name='tags', blank=True)
    draft = models.BooleanField(default=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.slug is None:
            self.slug = self.title.lower()
            self.slug = self.slug.strip(".,!\"*?:;~=()[]{}/&%+^#$'`<>|\\_")
            self.slug = self.slug.replace(" ", "-").replace('İ', 'i') \
                .replace('ş', 's').replace('ı', 'i').replace('ç', 'c') \
                .replace('ö', 'o').replace('ü', 'u').replace('ğ', 'g').replace('ş', 's')

        if self.hero_img is not None:
            image = Image.open(self.hero_img)

            if image.height > 1152 or image.width > 1152:
                output = photo_resizer(image, 780)
                self.hero_img = InMemoryUploadedFile(output, 'ImageField',
                                                     "%s.jpg" % self.hero_img.name.split('.')[
                                                         0],
                                                     'image/jpeg', sys.getsizeof(output), None)
            self.hero_img = photo_resizer(self.hero_img, 1152)

        super(Post, self).save(*args, **kwargs)


class Comment(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    body = models.TextField()
    name = models.CharField(max_length=75, help_text=_('Your Name...'))
    email = models.EmailField(help_text=_('Your Email...'))
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.body[:50]

    class Meta:
        ordering = ('-created_at',)


class Tag(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name = models.CharField(max_length=25)

    def save(self, *args, **kwargs):
        if self.name is not None:
            self.name = self.name.lower()
        super(Tag, self).save(*args, **kwargs)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
