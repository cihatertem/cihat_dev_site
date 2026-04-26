import sys
import uuid

from django.contrib.auth.models import AbstractUser
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from PIL import Image

from base.utils import photo_resizer, work_directory_path


class User(AbstractUser):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )


# Create your models here.
class Skill(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    skill = models.CharField(max_length=30, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.skill


class Work(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.CharField(max_length=200, null=True, blank=True)
    address = models.URLField(
        max_length=2000, null=True, blank=True, verbose_name="Work's URL"
    )
    work_title = models.CharField(max_length=200, null=True, blank=True)
    snapshot = models.ImageField(
        null=True,
        blank=True,
        default="default.jpg",
        upload_to=work_directory_path,
        verbose_name="Work's Landing Page Screenshot",
    )
    snapshot_alt = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Landing Page Screenshot Alt",
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.customer

    def _resize_snapshot(self):
        if not self.snapshot or getattr(self.snapshot, "_committed", True):
            return

        try:
            # Accessing self.snapshot.file can raise FileNotFoundError if the file doesn't exist.
            # Therefore we place this inside the try-except block.
            if not hasattr(self.snapshot, "file"):
                return

            with Image.open(self.snapshot) as image:
                if image.height <= 250 and image.width <= 250:
                    return

                output = photo_resizer(image, 250)
                self.snapshot = InMemoryUploadedFile(
                    output,
                    "ImageField",
                    "%s.jpg" % self.snapshot.name.split(".")[0],
                    "image/jpeg",
                    sys.getsizeof(output),
                    None,
                )
        except FileNotFoundError:
            pass

    def save(self, *args, **kwargs):
        self._resize_snapshot()
        return super().save(*args, **kwargs)
