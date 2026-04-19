import os

from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from base.models import Skill, User, Work
from base.utils import CAPTCHA_SESSION_KEY


class HomePageViewTests(TestCase):
    def setUp(self):
        # Clear cache since the view caches data
        cache.clear()

        self.client = Client()
        self.url = reverse("base:home")
        self.test_email = "testuser@example.com"

        # Set environment variable
        self.original_email = os.environ.get("EMAIL")
        os.environ["EMAIL"] = self.test_email

        # Create user and related data
        self.user = User.objects.create_user(
            username="testuser", email=self.test_email, password="password123"
        )
        self.skill = Skill.objects.create(user=self.user, skill="Python")

        # Avoid custom save() method side effects
        self.work = Work()
        self.work.user = self.user
        self.work.customer = "Test Customer"
        Work.objects.bulk_create([self.work])
        self.work = Work.objects.first()

    def tearDown(self):
        if self.original_email is not None:
            os.environ["EMAIL"] = self.original_email
        else:
            del os.environ["EMAIL"]
        cache.clear()

    def test_home_page_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/home.html")
        self.assertIn("skills", response.context)
        self.assertIn("works", response.context)
        self.assertEqual(list(response.context["skills"]), [self.skill])
        self.assertEqual(list(response.context["works"]), [self.work])
        self.assertIn("num1", response.context)
        self.assertIn("num2", response.context)
        self.assertIn(CAPTCHA_SESSION_KEY, self.client.session)

    def test_home_page_post_invalid_captcha(self):
        data = {
            "name": "Test Name",
            "subject": "Test Subject",
            "email": "sender@example.com",
            "body": "Test Body",
            "captcha": "999",  # Incorrect
            "website": "",
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)

        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "Toplam alanı boş ya da hatalı. Lütfen tekrar deneyin."
        )

    def test_home_page_post_success(self):
        response = self.client.get(self.url)
        captcha_answer = self.client.session.get(CAPTCHA_SESSION_KEY)

        data = {
            "name": "Test Name",
            "subject": "Test Subject",
            "email": "sender@example.com",
            "body": "Test Body",
            "captcha": str(captcha_answer),
            "website": "",
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Subject")
        self.assertIn("Test Body", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, [self.test_email])

        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue(
            str(messages[0]).startswith("Your message was sent successfully.")
        )

    def test_home_page_post_honeypot(self):
        response = self.client.get(self.url)
        captcha_answer = self.client.session.get(CAPTCHA_SESSION_KEY)

        data = {
            "name": "Spammer",
            "subject": "Spam",
            "email": "spammer@example.com",
            "body": "Spam body",
            "captcha": str(captcha_answer),
            "website": "http://spam.com",  # Honeypot filled
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)

        self.assertEqual(len(mail.outbox), 0)

        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "Your message was sent successfully.\nThank you!"
        )

    @override_settings(RATELIMIT_ENABLE=True)
    def test_home_page_post_rate_limited(self):
        # We need to simulate rate limiting
        # django-ratelimit needs a REMOTE_ADDR
        ip = "127.0.0.1"

        response = self.client.get(self.url, REMOTE_ADDR=ip)
        captcha_answer = self.client.session.get(CAPTCHA_SESSION_KEY)

        data = {
            "name": "Test",
            "subject": "Test",
            "email": "sender@example.com",
            "body": "Test",
            "captcha": str(captcha_answer),
            "website": "",
        }

        # 1st request
        self.client.post(self.url, data, REMOTE_ADDR=ip)

        # 2nd request
        self.client.get(self.url, REMOTE_ADDR=ip)
        data["captcha"] = str(self.client.session.get(CAPTCHA_SESSION_KEY))
        self.client.post(self.url, data, REMOTE_ADDR=ip)

        # 3rd request should hit the rate limit (2/m)
        self.client.get(self.url, REMOTE_ADDR=ip)
        data["captcha"] = str(self.client.session.get(CAPTCHA_SESSION_KEY))
        response = self.client.post(self.url, data, REMOTE_ADDR=ip)

        self.assertRedirects(response, self.url)

        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Çok fazla istek gönderdiniz" in str(m) for m in messages))
