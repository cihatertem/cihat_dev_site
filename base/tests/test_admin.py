from django.contrib import admin
from django.test import SimpleTestCase

from base.admin import SkillsAdmin, WorksAdmin
from base.models import Skill, User, Work


class AdminRegistrationTests(SimpleTestCase):
    def test_user_registered(self):
        self.assertTrue(admin.site.is_registered(User))

    def test_work_registered(self):
        self.assertTrue(admin.site.is_registered(Work))
        self.assertIsInstance(admin.site._registry[Work], WorksAdmin)

    def test_work_admin_config(self):
        self.assertEqual(WorksAdmin.ordering, ["-created"])
        self.assertEqual(WorksAdmin.list_display, ["work_title", "address", "created"])

    def test_skill_registered(self):
        self.assertTrue(admin.site.is_registered(Skill))
        self.assertIsInstance(admin.site._registry[Skill], SkillsAdmin)

    def test_skill_admin_config(self):
        self.assertEqual(SkillsAdmin.ordering, ["-created"])
        self.assertEqual(SkillsAdmin.list_display, ["skill", "created"])
