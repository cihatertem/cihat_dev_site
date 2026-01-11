from django.shortcuts import render, redirect
from .models import User
from .utils import get_client_ip, client_ip_key
import os
from django.core.mail import send_mail
from django.contrib import messages
from django_ratelimit.decorators import ratelimit

# Create your views here.

CONTACT_RATE_LIMIT = "2/m"
CONTACT_RATE_LIMIT_KEY = "ip"


@ratelimit(
    key=client_ip_key,
    rate=CONTACT_RATE_LIMIT,
    block=False,
    method=["POST"],
)
def home_page(request):
    template = 'base/home.html'
    user_email = os.getenv('EMAIL')
    user = User.objects.get(email=user_email)
    skills = user.skill_set.all()
    works = user.work_set.all()
    context = {
        'skills': skills,
        'works': works
    }

    if request.method == "POST":
        if getattr(request, "limited", False):
            messages.error(
                request,
                "Çok fazla istek gönderdiniz. Lütfen biraz sonra tekrar deneyin.",
            )
            return redirect("base:home")

        name = request.POST.get("name")
        subject = request.POST.get("subject")
        email = request.POST.get("email")
        body = request.POST.get("body")
        website = request.POST.get("website","")

        if website.strip():
            messages.success(
                request,
                "Your message was sent successfully.\nThank you!")

            return redirect("base:home")

        ip_address = get_client_ip(request)

        send_mail(
            subject,
            f"""
            From {name}, {email}, {ip_address},\n
            Subject {subject},\n
            {body}\n
            Site: www.cihatertem.dev
            """,
            email,
            (user_email,),
            fail_silently=False,
        )
        messages.success(
            request, "Your message was sent successfully.\nWe will touch \
            you back soon.")

        return redirect("base:home")

    return render(request, template, context)
