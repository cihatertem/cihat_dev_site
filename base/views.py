import os

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from .forms import ContactForm
from .models import User
from .utils import (
    CAPTCHA_SESSION_KEY,
    BoundedExecutor,
    _generate_captcha,
    captcha_is_valid,
    client_ip_key,
    get_client_ip,
)

# Create your views here.

email_executor = BoundedExecutor(max_workers=5, max_queue=10)


def _process_contact_post(request, user_email):
    """Handles the POST request logic for the contact form."""
    if getattr(request, "limited", False):
        messages.error(
            request,
            "Çok fazla istek gönderdiniz. Lütfen biraz sonra tekrar deneyin.",
        )
        return redirect("base:home")

    if not captcha_is_valid(request):
        messages.error(request, "Toplam alanı boş ya da hatalı. Lütfen tekrar deneyin.")
        return redirect("base:home")

    request.session.pop(CAPTCHA_SESSION_KEY, None)

    form = ContactForm(request.POST)
    if form.is_valid():
        name = form.cleaned_data.get("name")
        subject = form.cleaned_data.get("subject")
        email = form.cleaned_data.get("email")
        body = form.cleaned_data.get("body")
        website = form.cleaned_data.get("website", "")

        if website.strip():
            messages.success(request, "Your message was sent successfully.\nThank you!")

            return redirect("base:home")

        ip_address = get_client_ip(request)

        return _send_contact_email(
            request, name, subject, email, body, user_email, ip_address
        )

    return form


def _send_contact_email(request, name, subject, email, body, user_email, ip_address):
    """Helper function to create and send the contact email."""
    email_message = EmailMessage(
        subject,
        f"""
        From {name}, {email}, {ip_address},\n
        Subject {subject},\n
        {body}\n
        Site: {request.get_host()}
        """,
        user_email,
        [user_email],
        reply_to=[email],
    )

    future = email_executor.submit(email_message.send, fail_silently=False)
    if future.done() and future.exception():
        messages.error(
            request,
            "Our system is currently busy. Please try again later.",
        )
    else:
        messages.success(
            request,
            "Your message was sent successfully.\nWe will touch you back soon.",
        )

    return redirect("base:home")


def _get_cached_home_data(user_email):
    def get_home_data():
        user = get_object_or_404(
            User.objects.prefetch_related("skill_set", "work_set"), email=user_email
        )
        skills = list(user.skill_set.all())
        works = list(user.work_set.all())
        return skills, works

    return cache.get_or_set("home_data", get_home_data, 60 * 15)


@ratelimit(
    key=client_ip_key,
    rate=settings.CONTACT_RATE_LIMIT,
    block=False,
    method=["POST"],
)
@require_http_methods(["GET", "POST"])
def home_page(request):
    template = "base/home.html"
    user_email = os.getenv("EMAIL")
    if not user_email:
        raise ImproperlyConfigured("EMAIL environment variable is not set")

    skills, works = _get_cached_home_data(user_email)
    context = {"skills": skills, "works": works}

    form = ContactForm()
    if request.method == "POST":
        result = _process_contact_post(request, user_email)
        if isinstance(result, ContactForm):
            form = result
        else:
            return result

    num_one, num_two = _generate_captcha(request)
    context["num1"] = num_one
    context["num2"] = num_two
    context["form"] = form

    return render(request, template, context)
