from http import HTTPStatus

from django.http import JsonResponse
from django.test import RequestFactory, TestCase

from base.utils import HealthCheckMiddleware


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
