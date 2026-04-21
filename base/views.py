from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from .utils import (
    client_ip_key,
)

# Create your views here.

CONTACT_RATE_LIMIT = "2/m"
CONTACT_RATE_LIMIT_KEY = "ip"


@ratelimit(
    key=client_ip_key,
    rate=CONTACT_RATE_LIMIT,
    block=False,
    method=["POST"],
)
@require_http_methods(["GET", "POST"])
def home_page(request):
    template = "base/home.html"
    user_email = os.getenv("EMAIL")

    context = cache.get("home_context")
    if not context:
        user = User.objects.get(email=user_email)
        skills = list(user.skill_set.all())
        works = list(user.work_set.all())
        context = {"skills": skills, "works": works}
        cache.set("home_context", context, 60 * 15)
    else:
        context = context.copy()

    if request.method == "POST":
        if getattr(request, "limited", False):
            messages.error(
                request,
                "Çok fazla istek gönderdiniz. Lütfen biraz sonra tekrar deneyin.",
            )
            return redirect("base:home")

        if not captcha_is_valid(request):
            messages.error(
                request, "Toplam alanı boş ya da hatalı. Lütfen tekrar deneyin."
            )
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
                messages.success(
                    request, "Your message was sent successfully.\nThank you!"
                )

                return redirect("base:home")

            ip_address = get_client_ip(request)

            email_message = EmailMessage(
                subject,
                f"""
            From {name}, {email}, {ip_address},\n
            Subject {subject},\n
            {body}\n
            Site: www.cihatertem.dev
            """,
                user_email,
                [user_email],
                reply_to=[email],
            )
            email_message.send(fail_silently=False)

            messages.success(
                request,
                "Your message was sent successfully.\nWe will touch \
            you back soon.",
            )
            import os

            from django.contrib import messages
            from django.core.cache import cache
            from django.core.mail import EmailMessage
            from django.shortcuts import redirect, render
            from django.views.decorators.http import require_http_methods
            from django_ratelimit.decorators import ratelimit

            from .forms import ContactForm
            from .models import User
            from .utils import (
                CAPTCHA_SESSION_KEY,
                _generate_captcha,
                captcha_is_valid,
                client_ip_key,
                get_client_ip,
            )

            # Create your views here.

            CONTACT_RATE_LIMIT = "2/m"
            CONTACT_RATE_LIMIT_KEY = "ip"

            @ratelimit(
                key=client_ip_key,
                rate=CONTACT_RATE_LIMIT,
                block=False,
                method=["POST"],
            )
            @require_http_methods(["GET", "POST"])
            def home_page(request):
                template = "base/home.html"
                user_email = os.getenv("EMAIL")

                context = cache.get("home_context")
                if not context:
                    user = User.objects.get(email=user_email)
                    skills = list(user.skill_set.all())
                    works = list(user.work_set.all())
                    context = {"skills": skills, "works": works}
                    cache.set("home_context", context, 60 * 15)
                else:
                    context = context.copy()

                if request.method == "POST":
                    if getattr(request, "limited", False):
                        messages.error(
                            request,
                            "Çok fazla istek gönderdiniz. Lütfen biraz sonra tekrar deneyin.",
                        )
                        return redirect("base:home")

                    if not captcha_is_valid(request):
                        messages.error(
                            request, "Toplam alanı boş ya da hatalı. Lütfen tekrar deneyin."
                        )
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
                            messages.success(
                                request, "Your message was sent successfully.\nThank you!"
                            )

                            return redirect("base:home")

                        ip_address = get_client_ip(request)

                        email_message = EmailMessage(
                            subject,
                            f"""
                        From {name}, {email}, {ip_address},\n
                        Subject {subject},\n
                        {body}\n
                        Site: www.cihatertem.dev
                        """,
                            user_email,
                            [user_email],
                            reply_to=[email],
                        )
                        email_message.send(fail_silently=False)

                        messages.success(
                            request,
                            "Your message was sent successfully.\nWe will touch you back soon.",
                        )

                        return redirect("base:home")

                num_one, num_two = _generate_captcha(request)
                context["num1"] = num_one
                context["num2"] = num_two

                return render(request, template, context)

            return redirect("base:home")

    num_one, num_two = _generate_captcha(request)
    context["num1"] = num_one
    context["num2"] = num_two

    return render(request, template, context)
