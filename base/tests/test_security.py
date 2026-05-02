from django.test import TestCase

from base.utils import work_directory_path


class SecurityTest(TestCase):
    def test_work_directory_path_traversal(self):
        class DummyInstance:
            customer = "../../etc/passwd"

        instance = DummyInstance()
        filename = "evil.jpg"

        result = work_directory_path(instance, filename)

        # We expect something like "works/etcpasswd/evil.jpg"
        parts = result.split("/")
        self.assertEqual(parts[0], "works")
        self.assertNotIn("..", parts)
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[2], filename)

    def test_work_directory_path_filename_traversal(self):
        class DummyInstance:
            customer = "acme"

        instance = DummyInstance()
        filename = "../../etc/passwd"

        result = work_directory_path(instance, filename)

        parts = result.split("/")
        self.assertEqual(parts[0], "works")
        self.assertEqual(parts[1], "acme")
        self.assertEqual(parts[2], "passwd")
        self.assertEqual(len(parts), 3)
