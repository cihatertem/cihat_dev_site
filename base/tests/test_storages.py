from django.test import SimpleTestCase

from base.storages import CustomS3ManifestStaticStorage


class CustomS3ManifestStaticStorageTest(SimpleTestCase):
    def test_manifest_strict_is_false(self):
        self.assertFalse(CustomS3ManifestStaticStorage.manifest_strict)
