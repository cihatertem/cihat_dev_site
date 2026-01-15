import ipaddress
import math
from io import BytesIO
from random import random

from http import HTTPStatus
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from PIL import Image, ImageOps

CAPTCHA_SESSION_KEY = "contact_captcha_answer"

class HealthCheckMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.META['PATH_INFO'] == '/ping':
            return JsonResponse({"response": "pong!"}, status=HTTPStatus.OK)

def work_directory_path(instance, filename: str) -> str:
    return 'works/{0}/{1}'.format(instance.customer, filename)


def photo_resizer(image: Image, size: int) -> BytesIO:
    output = BytesIO()
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.thumbnail((size, size))
    image = ImageOps.exif_transpose(image)
    image.save(output, format='JPEG', quality=100)
    output.seek(0)
    return output


def get_client_ip(request) -> str | None:
    remote = request.META.get("REMOTE_ADDR")
    if not remote:
        return None

    ra = ipaddress.ip_address(remote)

    trusted_nets = getattr(settings, "TRUSTED_PROXY_NETS", None) or []

    # Sadece trusted proxy'den geliyorsa XFF'e güven
    if trusted_nets and any(ra in net for net in trusted_nets):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()

    return remote

def client_ip_key(group, request):
    # request None olmasın, ip yoksa sabit değer ver
    return get_client_ip(request) or "unknown"


def _parse_int(value: str | None) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
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
    num_one = math.floor(random() * 10) + 1
    num_two = math.floor(random() * 10) + 1
    request.session[CAPTCHA_SESSION_KEY] = num_one + num_two
    return num_one, num_two