import os
from unittest.mock import mock_open, patch

from django.test import SimpleTestCase

from cihat_dev.settings import get_secret


class GetSecretTests(SimpleTestCase):
    @patch.dict(os.environ, {"MY_TEST_KEY": "my_secret_value\n"})
    @patch("os.path.isfile", return_value=False)
    def test_get_secret_env_var_no_file(self, mock_isfile):
        result = get_secret("MY_TEST_KEY")
        self.assertEqual(result, "my_secret_value")
        mock_isfile.assert_called_once_with("my_secret_value\n")

    @patch.dict(os.environ, {}, clear=True)
    @patch("os.path.isfile", return_value=False)
    def test_get_secret_default_value(self, mock_isfile):
        result = get_secret("MISSING_KEY", default="default_val\n")
        self.assertEqual(result, "default_val")
        mock_isfile.assert_called_once_with("default_val\n")

    @patch.dict(os.environ, {"FILE_KEY": "/path/to/secret.txt"})
    @patch("os.path.isfile", return_value=True)
    def test_get_secret_from_file(self, mock_isfile):
        m_open = mock_open(read_data="file_secret_value\nsecond_line")
        with patch("builtins.open", m_open):
            result = get_secret("FILE_KEY")

        self.assertEqual(result, "file_secret_value")
        mock_isfile.assert_called_once_with("/path/to/secret.txt")
        m_open.assert_called_once_with("/path/to/secret.txt")
