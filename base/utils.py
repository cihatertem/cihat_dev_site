import ipaddress
import os
import secrets
from http import HTTPStatus
from io import BytesIO

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.text import slugify
from PIL import Image, ImageOps

CAPTCHA_SESSION_KEY = "contact_captcha_answer"


class HealthCheckMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.META["PATH_INFO"] == "/ping":
            return JsonResponse({"response": "pong!"}, status=HTTPStatus.OK)


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


def get_client_ip(request) -> str | None:
    remote = request.META.get("REMOTE_ADDR")
    if not remote:
        return None

    try:
        ra = ipaddress.ip_address(remote)
    except ValueError:
        return remote

    trusted_nets = getattr(settings, "TRUSTED_PROXY_NETS", None) or []

    # Sadece trusted proxy'den geliyorsa XFF'i parse et
    if trusted_nets and any(ra in net for net in trusted_nets):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            ips = [ip.strip() for ip in xff.split(",")]
            # Sağdan sola (en son proxy'den istemciye doğru) ilerle
            for ip_str in reversed(ips):
                try:
                    ip_obj = ipaddress.ip_address(ip_str)
                except ValueError:
                    # Geçersiz IP formatı - güvenilmez kabul et
                    return "unknown"

                # Eğer bu IP trusted ağlardan birindeyse, önceki IP'ye geçmeye devam et.
                # Değilse, bulduğumuz ilk untrusted IP gerçek istemcidir.
                is_trusted = any(ip_obj in net for net in trusted_nets)
                if not is_trusted:
                    return ip_str

            # Tüm IP'ler trusted ise, en soldakini dönebiliriz.
            return ips[0]

    return remote


def client_ip_key(group, request):
    # request None olmasın, ip yoksa sabit değer ver
    return get_client_ip(request) or "unknown"


def _parse_int(value: str | None) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
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
