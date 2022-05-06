from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from base.utils import work_directory_path, photo_resizer
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


class User(AbstractUser):
    __slot__ = "id"
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)


# Create your models here.
class Skill(models.Model):
    __slot__ = "id", "user", "skill", "created"
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    skill = models.CharField(max_length=30, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.skill


class Work(models.Model):
    __slot__ = "id", "user", "customer", "address", "work_title", "snapshot", "snapshot_alt", "created"
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.CharField(max_length=200, null=True, blank=True)
    address = models.URLField(
        max_length=2000, null=True, blank=True, verbose_name="Work's URL")
    work_title = models.CharField(max_length=200, null=True, blank=True)
    snapshot = models.ImageField(null=True, blank=True, default="default.jpg", upload_to=work_directory_path,
                                 verbose_name="Work's Landing Page Screenshot")
    snapshot_alt = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Landing Page Screenshot Alt")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.customer

    def save(self):
        image = Image.open(self.snapshot)

        if image.height > 250 or image.width > 250:
            output = photo_resizer(image, 250)
            self.snapshot = InMemoryUploadedFile(output, 'ImageField',
                                                 "%s.jpg" % self.snapshot.name.split('.')[
                                                     0],
                                                 'image/jpeg', sys.getsizeof(output), None)
        super(Work, self).save()


class SpamFilter(models.Model):
    __slot__ = "id", "keyword", "created"
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)
    keyword = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.keyword
