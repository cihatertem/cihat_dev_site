import os
from unittest.mock import mock_open, patch

from django.test import SimpleTestCase

from cihat_dev.settings import StripEnv, env
from cihat_dev.test_settings import MockGinIndex, MockSearchVector


class StripEnvTests(SimpleTestCase):
    def setUp(self):
        self.env = StripEnv()
        # Initialize an empty mapping for isolation
        self.env.ENVIRON = {}

    def test_get_value_strips_newlines(self):
        self.env.ENVIRON = {"TEST_VAR": "\ntest_value\n"}
        result = self.env.get_value("TEST_VAR")
        self.assertEqual(result, "test_value")

    def test_get_value_does_not_strip_non_strings(self):
        self.env.ENVIRON = {"TEST_INT": "123\n"}
        # Casting to int returns an integer, which is not a string, so it shouldn't be stripped
        result = self.env.get_value("TEST_INT", cast=int)
        self.assertEqual(result, 123)

    def test_get_value_strips_default_strings(self):
        # TEST_DEFAULT is not in ENVIRON, so it returns the default
        result = self.env.get_value("TEST_DEFAULT", default="\ndefault_val\n")
        self.assertEqual(result, "default_val")


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


class MockGinIndexTests(SimpleTestCase):
    def test_init_removes_config(self):
        index = MockGinIndex(
            fields=["field_name"], name="test_index", config="some_config"
        )
        self.assertEqual(index.fields, ["field_name"])
        self.assertEqual(index.name, "test_index")

    def test_create_sql_returns_empty_string(self):
        index = MockGinIndex(fields=["field_name"], name="test_index")
        sql = index.create_sql(model=None, schema_editor=None)
        self.assertEqual(sql, "")


class MockSearchVectorTests(SimpleTestCase):
    def test_resolve_expression_returns_self(self):
        vector = MockSearchVector("field_name")
        result = vector.resolve_expression()
        self.assertIs(result, vector)
