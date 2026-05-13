from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from base.models import User, Work
from base.utils import resize_work_snapshot_task


class WorkModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")

    def generate_test_image(self, width, height, color="blue"):
        img = Image.new("RGB", (width, height), color)
        img_io = BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)
        return SimpleUploadedFile(
            "test_image.jpg", img_io.read(), content_type="image/jpeg"
        )

    def test_save_resizes_large_image(self):
        large_image = self.generate_test_image(500, 300)
        work = Work(user=self.user, customer="Test Customer", snapshot=large_image)
        work.save()

        # Call the background task directly since transaction.on_commit won't
        # execute background threads predictably during simple test cases.
        resize_work_snapshot_task(work.id)
        work.refresh_from_db()

        with Image.open(work.snapshot) as img:
            # photo_resizer uses thumbnail((250, 250)) which maintains aspect ratio.
            # Max dimension should be 250.
            self.assertTrue(img.width <= 250)
            self.assertTrue(img.height <= 250)
            self.assertEqual(img.width, 250)

    def test_save_keeps_small_image(self):
        small_image = self.generate_test_image(100, 150)
        work = Work(user=self.user, customer="Test Customer", snapshot=small_image)
        work.save()

        resize_work_snapshot_task(work.id)
        work.refresh_from_db()

        with Image.open(work.snapshot) as img:
            self.assertEqual(img.width, 100)
            self.assertEqual(img.height, 150)

    def test_save_handles_missing_image(self):
        # Work without a snapshot file provided
        work = Work(user=self.user, customer="Test Customer", snapshot="")
        work.save()
        self.assertEqual(work.snapshot.name, "")

    def test_save_handles_default_image_not_found(self):
        work = Work(
            user=self.user,
            customer="Test Customer",
            # This triggers the default='default.jpg' case indirectly if not specified,
            # or explicitly testing a non-existent file.
            snapshot="non_existent.jpg",
        )
        work.save()
        self.assertEqual(work.snapshot.name, "non_existent.jpg")

    def test_resize_snapshot_catches_file_not_found(self):
        work = Work.objects.create(user=self.user, customer="Test Customer")

        class MockSnapshot:
            _committed = False
            name = "test.jpg"

            @property
            def file(self):
                raise FileNotFoundError("File not found")

            def save(self, *args, **kwargs):
                pass

        work.snapshot = MockSnapshot()

        # When bypassing standard fields for mocking, direct save fails in pre_save
        # so we will use bulk_create to bypass pre_save to get the mocked
        # object into the DB for the task, or just manually set the mock after fetch.

        # Let's override the object in python memory and test the task logic instead.
        # The task will fetch from db, so we need to mock Work.objects.get inside the task.
        import unittest.mock as mock

        with mock.patch("base.models.Work.objects.get", return_value=work):
            try:
                resize_work_snapshot_task(work.id)
            except FileNotFoundError:
                self.fail(
                    "resize_work_snapshot_task raised FileNotFoundError unexpectedly!"
                )
