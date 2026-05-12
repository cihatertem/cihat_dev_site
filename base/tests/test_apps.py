from django.apps import apps
from django.test import SimpleTestCase

from base.apps import BaseConfig


class BaseConfigTest(SimpleTestCase):
    def test_apps(self):
        self.assertEqual(BaseConfig.name, "base")
        self.assertEqual(BaseConfig.default_auto_field, "django.db.models.BigAutoField")

        app_config = apps.get_app_config("base")
        self.assertIsInstance(app_config, BaseConfig)
        self.assertEqual(app_config.name, "base")
        self.assertEqual(app_config.default_auto_field, "django.db.models.BigAutoField")
