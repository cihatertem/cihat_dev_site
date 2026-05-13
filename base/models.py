import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models, transaction

from base.utils import (
    image_executor,
    resize_work_snapshot_task,
    work_directory_path,
)


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

    def save(self, *args, **kwargs):
        should_resize = False
        # Avoid running logic if only other fields are updated
        update_fields = kwargs.get("update_fields", None)
        if update_fields is None or "snapshot" in update_fields:
            if self.snapshot and not getattr(self.snapshot, "_committed", True):
                should_resize = True

        super().save(*args, **kwargs)

        if should_resize:
            transaction.on_commit(
                lambda: image_executor.submit(resize_work_snapshot_task, self.id)
            )
