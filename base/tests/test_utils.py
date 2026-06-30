import ipaddress
import threading
from http import HTTPStatus
from unittest.mock import MagicMock, patch

from django.http import JsonResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from PIL import ExifTags, Image

from base.utils import (
    CAPTCHA_SESSION_KEY,
    BoundedExecutor,
    HealthCheckMiddleware,
    _generate_captcha,
    _parse_int,
    _parse_x_forwarded_for,
    captcha_is_valid,
    client_ip_key,
    get_client_ip,
    photo_resizer,
    work_directory_path,
)


class WorkDirectoryPathTest(TestCase):
    def test_work_directory_path(self):
        class DummyInstance:
            customer = "acme_corp"

        instance = DummyInstance()
        filename = "logo.png"

        result = work_directory_path(instance, filename)
        self.assertEqual(result, "works/acme_corp/logo.png")


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


class ParseIntTest(SimpleTestCase):
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

    def test_error_handling(self):
        self.assertIsNone(_parse_int(None))
        self.assertIsNone(_parse_int("abc"))

    def test_whitespace_strings(self):
        self.assertEqual(_parse_int(" 123 "), 123)
        self.assertEqual(_parse_int("\t456\n"), 456)


class ClientIpKeyTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_client_ip_key_with_ip(self):
        request = self.factory.get("/", REMOTE_ADDR="192.168.1.5")
        self.assertEqual(client_ip_key("test_group", request), "192.168.1.5")

    def test_client_ip_key_without_ip(self):
        request = self.factory.get("/")
        if "REMOTE_ADDR" in request.META:
            del request.META["REMOTE_ADDR"]
        self.assertEqual(client_ip_key("test_group", request), "unknown")


class ParseXForwardedForTest(SimpleTestCase):
    def setUp(self):
        self.trusted_nets = (ipaddress.ip_network("10.0.0.0/8"),)

    def test_all_invalid_ips(self):
        self.assertEqual(
            _parse_x_forwarded_for("invalid-ip, another-invalid", self.trusted_nets),
            "unknown",
        )

    def test_mixed_invalid_valid_ips(self):
        self.assertEqual(
            _parse_x_forwarded_for("192.168.1.1, invalid-ip", self.trusted_nets),
            "unknown",
        )

    def test_invalid_valid_ips_reverse(self):
        self.assertEqual(
            _parse_x_forwarded_for("invalid-ip, 10.0.0.5", self.trusted_nets),
            "unknown",
        )

    def test_all_trusted_ips(self):
        self.assertEqual(
            _parse_x_forwarded_for("10.0.0.1, 10.0.0.2", self.trusted_nets),
            "10.0.0.1",
        )

    def test_mixed_trusted_untrusted_ips(self):
        self.assertEqual(
            _parse_x_forwarded_for("192.168.1.1, 10.0.0.2", self.trusted_nets),
            "192.168.1.1",
        )

    def test_mixed_trusted_untrusted_ips_reverse(self):
        self.assertEqual(
            _parse_x_forwarded_for("10.0.0.1, 192.168.1.2", self.trusted_nets),
            "192.168.1.2",
        )

    def test_ips_with_spaces(self):
        self.assertEqual(
            _parse_x_forwarded_for(
                "192.168.1.1,  10.0.0.1 , 10.0.0.2 ", self.trusted_nets
            ),
            "192.168.1.1",
        )


class GetClientIpTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_missing_remote_addr(self):
        request = self.factory.get("/")
        if "REMOTE_ADDR" in request.META:
            del request.META["REMOTE_ADDR"]
        self.assertIsNone(get_client_ip(request))

    def test_get_client_ip_value_error(self):
        request = self.factory.get("/", REMOTE_ADDR="not_an_ip")
        self.assertEqual(get_client_ip(request), "unknown")

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
        self.assertEqual(get_client_ip(request), "unknown")

    def test_ipv6_normalization(self):
        # Test that functionally equivalent IPv6 strings are normalized to the same format
        request1 = self.factory.get("/", REMOTE_ADDR="2001:db8::1")
        request2 = self.factory.get(
            "/", REMOTE_ADDR="2001:0db8:0000:0000:0000:0000:0000:0001"
        )

        self.assertEqual(get_client_ip(request1), "2001:db8::1")
        self.assertEqual(get_client_ip(request2), "2001:db8::1")

    @override_settings(TRUSTED_PROXY_NETS=[ipaddress.ip_network("10.0.0.0/8")])
    def test_ipv6_normalization_in_xff(self):
        request1 = self.factory.get(
            "/",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="2001:db8::1",
        )
        request2 = self.factory.get(
            "/",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="2001:0db8:0000:0000:0000:0000:0000:0001",
        )

        self.assertEqual(get_client_ip(request1), "2001:db8::1")
        self.assertEqual(get_client_ip(request2), "2001:db8::1")


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


class GenerateCaptchaTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_generate_captcha(self):
        request = self.factory.get("/")
        request.session = {}

        num_one, num_two = _generate_captcha(request)

        # Assert returned values are integers between 1 and 10
        self.assertIsInstance(num_one, int)
        self.assertIsInstance(num_two, int)
        self.assertGreaterEqual(num_one, 1)
        self.assertLessEqual(num_one, 10)
        self.assertGreaterEqual(num_two, 1)
        self.assertLessEqual(num_two, 10)

        # Assert the session contains the sum of the two numbers
        self.assertIn(CAPTCHA_SESSION_KEY, request.session)
        self.assertEqual(request.session[CAPTCHA_SESSION_KEY], num_one + num_two)

    @patch("base.utils.secrets.randbelow")
    def test_generate_captcha_mocked(self, mock_randbelow):
        # Set mock side effects (returns 4, then 7)
        # randbelow(10) + 1 -> 5, 8
        mock_randbelow.side_effect = [4, 7]

        request = self.factory.get("/")
        request.session = {}

        num_one, num_two = _generate_captcha(request)

        # Assert the mocked values were used
        self.assertEqual(num_one, 5)
        self.assertEqual(num_two, 8)
        self.assertEqual(mock_randbelow.call_count, 2)

        # Assert the session contains the sum
        self.assertIn(CAPTCHA_SESSION_KEY, request.session)
        self.assertEqual(request.session[CAPTCHA_SESSION_KEY], 13)


class PhotoResizerTest(SimpleTestCase):
    def test_photo_resizer_rgba_conversion(self):
        # Create a dummy RGBA image
        img = Image.new("RGBA", (200, 200), (255, 0, 0, 255))
        output = photo_resizer(img, 100)

        # Open the output image and verify it's JPEG (which implies RGB mode)
        out_img = Image.open(output)
        self.assertEqual(out_img.format, "JPEG")
        self.assertEqual(out_img.mode, "RGB")
        self.assertEqual(out_img.size, (100, 100))

    def test_photo_resizer_p_conversion(self):
        # Create a dummy P (palette) image
        img = Image.new("P", (200, 200), 1)
        output = photo_resizer(img, 100)

        # Open the output image and verify it's JPEG
        out_img = Image.open(output)
        self.assertEqual(out_img.format, "JPEG")
        self.assertEqual(out_img.mode, "RGB")
        self.assertEqual(out_img.size, (100, 100))

    def test_photo_resizer_resizes_image(self):
        # Create a dummy RGB image with non-square dimensions
        img = Image.new("RGB", (300, 200), (0, 255, 0))
        output = photo_resizer(img, 100)

        # The thumbnail method should maintain aspect ratio
        out_img = Image.open(output)
        self.assertEqual(out_img.format, "JPEG")
        self.assertEqual(out_img.mode, "RGB")
        # 300/200 -> 100/67 (rounding)
        self.assertEqual(out_img.size, (100, 67))

    def test_photo_resizer_exif_transpose(self):
        # Create a dummy image
        img = Image.new("RGB", (300, 200), (0, 0, 255))

        # Get EXIF dict and set orientation to 6 (Rotated 90 degrees CCW)
        exif = img.getexif()
        orientation_tag = next(
            (k for k, v in ExifTags.TAGS.items() if v == "Orientation"), None
        )
        if orientation_tag:
            exif[orientation_tag] = 6

        # Save image with EXIF to buffer, then read it back so PIL parses EXIF
        from io import BytesIO

        b = BytesIO()
        img.save(b, format="JPEG", exif=exif)
        b.seek(0)
        img_with_exif = Image.open(b)

        # Original is 300x200, resized to 100x67.
        # Orientation 6 transposes the image, so output should be 67x100
        output = photo_resizer(img_with_exif, 100)

        out_img = Image.open(output)
        self.assertEqual(out_img.format, "JPEG")
        self.assertEqual(out_img.mode, "RGB")
        self.assertEqual(out_img.size, (67, 100))


class BoundedExecutorTest(SimpleTestCase):
    def test_bounded_executor_init(self):
        max_workers = 3
        max_queue = 5
        executor = BoundedExecutor(max_workers=max_workers, max_queue=max_queue)

        self.assertEqual(executor.executor._max_workers, max_workers)
        self.assertEqual(executor.semaphore._value, max_workers + max_queue)

    def test_bounded_executor_shutdown(self):
        executor = BoundedExecutor(max_workers=2, max_queue=2)
        executor.executor.shutdown = MagicMock()

        # Test default parameters
        executor.shutdown()
        executor.executor.shutdown.assert_called_once_with(
            wait=True, cancel_futures=False
        )

        executor.executor.shutdown.reset_mock()

        # Test explicit parameters
        executor.shutdown(wait=False, cancel_futures=True)
        executor.executor.shutdown.assert_called_once_with(
            wait=False, cancel_futures=True
        )

    def test_bounded_executor_real_shutdown(self):
        executor = BoundedExecutor(max_workers=1, max_queue=1)
        executor.shutdown()

        def dummy_task():
            pass

        with self.assertRaisesMessage(
            RuntimeError, "cannot schedule new futures after shutdown"
        ):
            executor.submit(dummy_task)

    def test_bounded_executor_submit_success(self):
        executor = BoundedExecutor(max_workers=1, max_queue=1)

        # Test successful path with args and kwargs
        def task_function(x, y, z=0):
            return x + y + z

        future1 = executor.submit(task_function, 1, 2, z=3)
        self.assertEqual(future1.result(), 6)

        # Test exception handling in task
        def failing_task():
            raise ValueError("Test error")

        future2 = executor.submit(failing_task)
        with self.assertRaisesMessage(ValueError, "Test error"):
            future2.result()

        # Test that semaphore is correctly released by sequentially submitting tasks
        # Capacity is max_workers(1) + max_queue(1) = 2.
        # We submit 3 tasks sequentially (waiting for each to finish)
        for i in range(3):
            future = executor.submit(task_function, i, 1)
            self.assertEqual(future.result(), i + 1)

        executor.shutdown()

    def test_bounded_executor_queue_full(self):
        executor = BoundedExecutor(max_workers=1, max_queue=1)
        event = threading.Event()

        def blocking_task():
            event.wait()
            return True

        # First task takes the worker
        executor.submit(blocking_task)
        # Second task fills the queue
        executor.submit(blocking_task)

        # Third task should fail immediately as the queue is full
        with self.assertLogs("base.utils", level="WARNING") as logs:
            f3 = executor.submit(blocking_task)

        self.assertIn("Task queue is full", str(f3.exception()))
        self.assertEqual(
            logs.output,
            [
                "WARNING:base.utils:BoundedExecutor queue full. Dropping task to prevent DoS."
            ],
        )

        # Verify that the third task returns a Future with RuntimeError
        with self.assertRaisesMessage(RuntimeError, "Task queue is full"):
            f3.result()

        # Cleanup
        event.set()
        executor.shutdown()

    def test_bounded_executor_queue_full_sync_check(self):
        executor = BoundedExecutor(max_workers=1, max_queue=1)
        event = threading.Event()

        def blocking_task():
            event.wait()
            return True

        # First task takes the worker
        executor.submit(blocking_task)
        # Second task fills the queue
        executor.submit(blocking_task)

        # Third task should fail immediately
        f3 = executor.submit(blocking_task)

        # Verify that we can synchronously check for the exception using done() and exception()
        self.assertTrue(f3.done())
        self.assertIsInstance(f3.exception(), RuntimeError)
        self.assertEqual(str(f3.exception()), "Task queue is full")

        # Cleanup
        event.set()
        executor.shutdown()
