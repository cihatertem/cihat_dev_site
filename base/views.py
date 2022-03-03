from django.shortcuts import render, redirect
from .models import User
import os
from dotenv import load_dotenv
from django.core.mail import send_mail
from django.contrib import messages

load_dotenv()


# Create your views here.

def home_page(request):
    template = 'base/home.html'
    user = User.objects.get(email=os.getenv('EMAIL'))
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
        send_mail(
            subject,
            f"""
            From {name}, {email},\n
            Subject {subject},\n
            {body}
            """,
            email,
            ['cihatertem@gmail.com'],
            fail_silently=False,
        )
        messages.success(request, "Your message was sent successfully.\nWe will touch you back soon.")

        return redirect("base:home")

    return render(request, template, context)
