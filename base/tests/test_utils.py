import ipaddress
from http import HTTPStatus

from django.http import JsonResponse
from django.test import RequestFactory, TestCase, override_settings

from base.utils import (
    CAPTCHA_SESSION_KEY,
    HealthCheckMiddleware,
    _parse_int,
    captcha_is_valid,
    get_client_ip,
)


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


class GetClientIpTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_missing_remote_addr(self):
        request = self.factory.get("/")
        if "REMOTE_ADDR" in request.META:
            del request.META["REMOTE_ADDR"]
        self.assertIsNone(get_client_ip(request))

    def test_no_trusted_proxies(self):
        request = self.factory.get("/", REMOTE_ADDR="192.168.1.5")
        self.assertEqual(get_client_ip(request), "192.168.1.5")

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_remote_addr_not_in_trusted(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="192.168.1.5", HTTP_X_FORWARDED_FOR="203.0.113.195"
        )
        self.assertEqual(get_client_ip(request), "192.168.1.5")

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_remote_addr_in_trusted_no_xff(self):
        request = self.factory.get("/", REMOTE_ADDR="10.0.0.5")
        self.assertEqual(get_client_ip(request), "10.0.0.5")

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_remote_addr_in_trusted_with_xff(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="10.0.0.5", HTTP_X_FORWARDED_FOR="203.0.113.195"
        )
        self.assertEqual(get_client_ip(request), "203.0.113.195")

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_remote_addr_in_trusted_with_xff_multiple(self):
        request = self.factory.get(
            "/",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="203.0.113.195, 198.51.100.1, 192.0.2.1",
        )
        self.assertEqual(get_client_ip(request), "192.0.2.1")

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_spoofing_xff(self):
        # Client 203.0.113.1 tries to spoof its IP by sending Fake1, Fake2
        # It connects through trusted proxy 10.0.0.5
        request = self.factory.get(
            "/",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="8.8.8.8, 1.1.1.1, 203.0.113.1",
        )
        self.assertEqual(get_client_ip(request), "203.0.113.1")

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_xff_only_trusted_proxies(self):
        # The request comes from 10.0.0.5
        # The XFF header only contains other trusted proxies.
        # We expect the leftmost proxy to be returned.
        request = self.factory.get(
            "/",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="10.1.1.1, 10.2.2.2, 10.3.3.3",
        )
        self.assertEqual(get_client_ip(request), "10.1.1.1")

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_xff_with_invalid_ip(self):
        # The XFF header contains invalid IPs
        request = self.factory.get(
            "/",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="192.168.1.5, invalid-ip",
        )
        self.assertEqual(get_client_ip(request), "invalid-ip")


class CaptchaIsValidTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_captcha_is_valid_success(self):
        request = self.factory.post("/", data={"captcha": "15"})
        request.session = {CAPTCHA_SESSION_KEY: "15"}
        self.assertTrue(captcha_is_valid(request))

    def test_captcha_is_valid_mismatch(self):
        request = self.factory.post("/", data={"captcha": "10"})
        request.session = {CAPTCHA_SESSION_KEY: "15"}
        self.assertFalse(captcha_is_valid(request))

    def test_captcha_is_valid_missing_session(self):
        request = self.factory.post("/", data={"captcha": "15"})
        request.session = {}
        self.assertFalse(captcha_is_valid(request))

    def test_captcha_is_valid_missing_post(self):
        request = self.factory.post("/", data={})
        request.session = {CAPTCHA_SESSION_KEY: "15"}
        self.assertFalse(captcha_is_valid(request))

    def test_captcha_is_valid_non_integer_post(self):
        request = self.factory.post("/", data={"captcha": "abc"})
        request.session = {CAPTCHA_SESSION_KEY: "15"}
        self.assertFalse(captcha_is_valid(request))

    def test_captcha_is_valid_non_integer_session(self):
        request = self.factory.post("/", data={"captcha": "15"})
        request.session = {CAPTCHA_SESSION_KEY: "abc"}
        self.assertFalse(captcha_is_valid(request))
