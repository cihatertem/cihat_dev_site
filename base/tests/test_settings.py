import os
from unittest.mock import mock_open, patch

from django.test import SimpleTestCase

from cihat_dev.settings import env


class GetSecretTests(SimpleTestCase):
    @patch.dict(os.environ, {"MY_TEST_KEY": "my_secret_value\n"})
    def test_get_secret_env_var_no_file(self):
        # By mocking environ, env(...) reads it from os.environ
        # However, because FileAwareMapping grabs from os.environ natively, we can just patch os.environ directly.
        # But environ.Env evaluates from self.ENVIRON.
        with patch.object(env, "ENVIRON", os.environ):
            result = env.str("MY_TEST_KEY")
            self.assertEqual(result, "my_secret_value")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_secret_default_value(self):
        with patch.object(env, "ENVIRON", os.environ):
            result = env.str("MISSING_KEY", default="default_val\n")
            self.assertEqual(result, "default_val")

    @patch.dict(os.environ, {"FILE_KEY_FILE": "/path/to/secret.txt"})
    @patch("os.path.isfile", return_value=True)
    def test_get_secret_from_file(self, mock_isfile):
        m_open = mock_open(read_data="file_secret_value\nsecond_line")
        # We need to simulate how FileAwareMapping works
        from environ.fileaware_mapping import FileAwareMapping

        test_env_mapping = FileAwareMapping()
        with patch("builtins.open", m_open):
            with patch.object(env, "ENVIRON", test_env_mapping):
                result = env.str("FILE_KEY")

        self.assertEqual(result, "file_secret_value\nsecond_line")
        m_open.assert_called_once_with("/path/to/secret.txt", encoding="utf-8")
