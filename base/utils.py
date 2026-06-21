import bisect
import concurrent.futures
import functools
import ipaddress
import logging
import os
import secrets
import threading
from http import HTTPStatus
from io import BytesIO

from django.conf import settings
from django.http import JsonResponse
from django.utils.text import slugify
from PIL import Image, ImageOps

CAPTCHA_SESSION_KEY = "contact_captcha_answer"


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.META["PATH_INFO"] == "/ping":
            return JsonResponse({"response": "pong!"}, status=HTTPStatus.OK)
        return self.get_response(request)


def work_directory_path(instance, filename: str) -> str:
    customer_slug = slugify(instance.customer) or "unknown"
    safe_filename = os.path.basename(filename)
    return "works/{0}/{1}".format(customer_slug, safe_filename)


def photo_resizer(image: Image, size: int) -> BytesIO:
    output = BytesIO()
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.thumbnail((size, size))
    image = ImageOps.exif_transpose(image)
    image.save(output, format="JPEG", quality=100)
    output.seek(0)
    return output


class IPRangeChecker:
    __slots__ = ["v4_nets", "v6_nets", "original_nets"]

    def __init__(self, networks: tuple):
        self.original_nets = networks
        self.v4_nets = []
        self.v6_nets = []

        for net in ipaddress.collapse_addresses(networks):
            if net.version == 4:
                self.v4_nets.append(net)
            else:
                self.v6_nets.append(net)

    def __contains__(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        nets = self.v4_nets if ip.version == 4 else self.v6_nets
        if not nets:
            return False

        idx = bisect.bisect_right(nets, ip, key=lambda net: net.network_address) - 1
        if idx >= 0 and ip in nets[idx]:
            return True
        return False


@functools.lru_cache(maxsize=1)
def _get_ip_range_checker(trusted_nets_tuple: tuple) -> IPRangeChecker:
    return IPRangeChecker(trusted_nets_tuple)


@functools.lru_cache(maxsize=1024)
def _is_ip_trusted(ip_str: str, trusted_nets_tuple: tuple) -> bool | None:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return None
    checker = _get_ip_range_checker(trusted_nets_tuple)
    return ip_obj in checker


def _parse_x_forwarded_for(xff: str, trusted_nets_tuple: tuple) -> str:
    ips = xff.split(",")
    # Sağdan sola (en son proxy'den istemciye doğru) ilerle
    for ip_raw in reversed(ips):
        ip_str = ip_raw.strip()
        trusted = _is_ip_trusted(ip_str, trusted_nets_tuple)
        if trusted is None:
            # Geçersiz IP formatı - güvenilmez kabul et
            return "unknown"
        if not trusted:
            # Değilse, bulduğumuz ilk untrusted IP gerçek istemcidir.
            return ip_str

    # Tüm IP'ler trusted ise, en soldakini dönebiliriz.
    return ips[0].strip()


def get_client_ip(request) -> str | None:
    remote = request.META.get("REMOTE_ADDR")
    if not remote:
        return None

    try:
        ra = ipaddress.ip_address(remote)
    except ValueError:
        return "unknown"

    trusted_nets = getattr(settings, "TRUSTED_PROXY_NETS", None) or []

    if trusted_nets:
        trusted_nets_tuple = tuple(trusted_nets)
        checker = _get_ip_range_checker(trusted_nets_tuple)

        # Sadece trusted proxy'den geliyorsa XFF'i parse et
        if ra in checker:
            xff = request.META.get("HTTP_X_FORWARDED_FOR")
            if xff:
                return _parse_x_forwarded_for(xff, trusted_nets_tuple)

    return remote


def client_ip_key(group, request):
    # request None olmasın, ip yoksa sabit değer ver
    return get_client_ip(request) or "unknown"


def _parse_int(value: str | None) -> int | None:
    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def captcha_is_valid(request) -> bool:
    """
    Returns True if posted captcha matches expected answer in session.
    Missing/invalid values return False.
    """
    expected = _parse_int(request.session.get(CAPTCHA_SESSION_KEY))
    got = _parse_int(request.POST.get("captcha"))

    return expected is not None and got is not None and got == expected


def _generate_captcha(request):
    num_one = secrets.randbelow(10) + 1
    num_two = secrets.randbelow(10) + 1
    request.session[CAPTCHA_SESSION_KEY] = num_one + num_two
    return num_one, num_two


logger = logging.getLogger(__name__)


class BoundedExecutor:
    """
    A ThreadPoolExecutor with a bounded queue.
    Prevents memory exhaustion/DoS from unlimited task queuing.
    """

    def __init__(self, max_workers: int, max_queue: int):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = threading.Semaphore(max_workers + max_queue)

    def submit(self, fn, *args, **kwargs):
        if not self.semaphore.acquire(blocking=False):
            logger.warning("BoundedExecutor queue full. Dropping task to prevent DoS.")
            f = concurrent.futures.Future()
            f.set_exception(RuntimeError("Task queue is full"))
            return f

        def release_and_run():
            try:
                return fn(*args, **kwargs)
            finally:
                self.semaphore.release()

        return self.executor.submit(release_and_run)

    def shutdown(self, wait=True, *, cancel_futures=False):
        self.executor.shutdown(wait=wait, cancel_futures=cancel_futures)


image_executor = BoundedExecutor(max_workers=2, max_queue=10)


def resize_work_snapshot_task(work_id):
    try:
        from django.core.files.base import ContentFile
        from PIL import Image

        from base.models import Work

        work = Work.objects.get(id=work_id)
        if not work.snapshot:
            return

        try:
            if not hasattr(work.snapshot, "file"):
                return
        except FileNotFoundError:
            return

        with Image.open(work.snapshot) as image:
            if image.height <= 250 and image.width <= 250:
                return

            output = photo_resizer(image, 250)

            old_name = work.snapshot.name
            new_file_name = "%s.jpg" % work.snapshot.name.split("/")[-1].split(".")[0]

            work.snapshot.save(new_file_name, ContentFile(output.read()), save=False)
            work.save(update_fields=["snapshot"])

            if work.snapshot.name != old_name:
                work.snapshot.storage.delete(old_name)
    except Exception as e:
        logger.error(f"Error resizing work snapshot {work_id}: {e}")
