import ipaddress

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from base.middlewares import TrustedProxyMiddleware


class TrustedProxyMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.get_response = lambda request: HttpResponse()
        self.middleware = TrustedProxyMiddleware(self.get_response)

    def _get_request_with_headers(self, remote_addr=None):
        request = self.factory.get("/")
        meta = {
            "HTTP_X_FORWARDED_FOR": "203.0.113.195",
            "HTTP_X_FORWARDED_HOST": "example.com",
            "HTTP_X_FORWARDED_PROTO": "https",
        }
        request.META.update(meta)
        if remote_addr is not None:
            request.META["REMOTE_ADDR"] = remote_addr
        else:
            request.META.pop("REMOTE_ADDR", None)
        return request

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_untrusted_proxy_strips_headers(self):
        request = self._get_request_with_headers(remote_addr="192.168.1.100")
        self.middleware(request)

        self.assertNotIn("HTTP_X_FORWARDED_FOR", request.META)
        self.assertNotIn("HTTP_X_FORWARDED_HOST", request.META)
        self.assertNotIn("HTTP_X_FORWARDED_PROTO", request.META)

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_trusted_proxy_keeps_headers(self):
        request = self._get_request_with_headers(remote_addr="10.0.0.5")
        self.middleware(request)

        self.assertEqual(request.META.get("HTTP_X_FORWARDED_FOR"), "203.0.113.195")
        self.assertEqual(request.META.get("HTTP_X_FORWARDED_HOST"), "example.com")
        self.assertEqual(request.META.get("HTTP_X_FORWARDED_PROTO"), "https")

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_missing_remote_addr_strips_headers(self):
        request = self._get_request_with_headers()
        self.middleware(request)

        self.assertNotIn("HTTP_X_FORWARDED_FOR", request.META)

    @override_settings(TRUSTED_PROXY_NETS=[])
    def test_empty_trusted_nets_strips_headers(self):
        request = self._get_request_with_headers(remote_addr="10.0.0.5")
        self.middleware(request)

        self.assertNotIn("HTTP_X_FORWARDED_FOR", request.META)

    def test_no_trusted_nets_setting_strips_headers(self):
        with self.settings(TRUSTED_PROXY_NETS=None):
            request = self._get_request_with_headers(remote_addr="10.0.0.5")
            self.middleware(request)

            self.assertNotIn("HTTP_X_FORWARDED_FOR", request.META)

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_invalid_remote_addr_strips_headers(self):
        request = self._get_request_with_headers(remote_addr="not_an_ip")
        self.middleware(request)

        self.assertNotIn("HTTP_X_FORWARDED_FOR", request.META)
