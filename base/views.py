from django.shortcuts import render, redirect
from .models import User
from .utils import get_client_ip
import os
from django.core.mail import send_mail
from django.contrib import messages


# Create your views here.

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
