from PIL import Image, ImageOps
from io import BytesIO
from base import models
from django.http import HttpRequest
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from http import HTTPStatus


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


def spam_checker(mail_body) -> bool | None:
    spam_keywords = models.SpamFilter.objects.all()

    spam_list = []

    for keyword in spam_keywords:
        spam_list.append(keyword.keyword.lower())

    body_words = mail_body.strip().split(" ")
    stripped_words = []

    for body_word in body_words:
        body_word = body_word.strip(".?!:;* '\"-_,`").lower()
        if not body_word:
            continue
        stripped_words.append(body_word)

    for stripped_word in stripped_words:
        if stripped_word in spam_list:
            return True


def get_client_ip(request: HttpRequest) -> dict[str, str]:
    return {
        'REMOTE_ADDR': request.META.get('REMOTE_ADDR'),
        'HTTP_X_FORWARDED_FOR': request.META.get('HTTP_X_FORWARDED_FOR')
    }
