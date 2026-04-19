from http import HTTPStatus

from django.http import JsonResponse
from django.test import RequestFactory, TestCase

from base.utils import HealthCheckMiddleware, _parse_int


class HealthCheckMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.get_response = lambda r: JsonResponse({"status": "ok"})
        self.middleware = HealthCheckMiddleware(self.get_response)

    def test_ping_returns_pong(self):
        # Create a request to /ping
        request = self.factory.get("/ping")

        # Testing the middleware as a callable
        response = self.middleware(request)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.content, b'{"response": "pong!"}')
        self.assertIsInstance(response, JsonResponse)

    def test_other_path_not_intercepted(self):
        # Create a request to another path
        request = self.factory.get("/")

        # Testing the middleware as a callable
        response = self.middleware(request)

        # It should return the response from the next handler
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.content, b'{"status": "ok"}')


class ParseIntTest(TestCase):
    def test_valid_integers(self):
        self.assertEqual(_parse_int("123"), 123)
        self.assertEqual(_parse_int("-456"), -456)
        self.assertEqual(_parse_int("0"), 0)

    def test_none_and_empty_string(self):
        self.assertIsNone(_parse_int(None))
        self.assertIsNone(_parse_int(""))

    def test_value_error(self):
        self.assertIsNone(_parse_int("abc"))
        self.assertIsNone(_parse_int("12.3"))

    def test_type_error(self):
        self.assertIsNone(_parse_int([1, 2, 3]))
        self.assertIsNone(_parse_int({"a": 1}))
