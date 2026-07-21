import sys
from unittest.mock import patch

from django.test import SimpleTestCase

import manage


class ManagePyTests(SimpleTestCase):
    @patch("django.core.management.execute_from_command_line")
    def test_main_success(self, mock_execute):
        with patch.object(sys, "argv", ["manage.py", "help"]):
            manage.main()
            mock_execute.assert_called_once_with(["manage.py", "help"])

    def test_main_import_error(self):
        # We need to simulate the ImportError raised when importing
        # execute_from_command_line from django.core.management
        # We can do this by patching sys.modules
        with patch.dict(sys.modules, {"django.core.management": None}):
            with self.assertRaisesMessage(ImportError, "Couldn't import Django"):
                manage.main()
