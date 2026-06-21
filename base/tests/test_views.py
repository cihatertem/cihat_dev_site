import time
from unittest.mock import MagicMock, patch

from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from base.models import Skill, User, Work
from base.utils import CAPTCHA_SESSION_KEY
from base.views import _get_cached_home_data


@override_settings(CONTACT_EMAIL="testuser@example.com")
class HomePageViewTests(TestCase):
    def setUp(self):
        # Clear cache since the view caches data
        cache.clear()

        self.client = Client()
        self.url = reverse("base:home")
        self.test_email = "testuser@example.com"

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
        mail.outbox.clear()
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

    def test_home_page_post_invalid_form(self):
        response = self.client.get(self.url)
        captcha_answer = self.client.session.get(CAPTCHA_SESSION_KEY)

        data = {
            # Missing required fields like 'name', 'subject', 'email', 'body'
            "captcha": str(captcha_answer),
            "website": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/home.html")
        self.assertIn("skills", response.context)
        self.assertIn("works", response.context)
        self.assertIn("num1", response.context)
        self.assertIn("num2", response.context)
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].errors)
        self.assertContains(response, "form-errors")

    def test_home_page_post_queue_full(self):
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

        import concurrent.futures
        from unittest.mock import patch

        future = concurrent.futures.Future()
        future.set_exception(RuntimeError("Task queue is full"))

        with patch("base.views.email_executor.submit", return_value=future):
            response = self.client.post(self.url, data)

        self.assertRedirects(response, self.url)

        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "Our system is currently busy. Please try again later."
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
        mail.outbox.clear()
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)

        # Wait dynamically for email thread to finish
        timeout = 2.0
        start_time = time.time()
        while len(mail.outbox) == 0 and time.time() - start_time < timeout:
            time.sleep(0.01)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Subject")
        self.assertIn("Test Body", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, [self.test_email])
        self.assertEqual(mail.outbox[0].from_email, self.test_email)
        self.assertEqual(mail.outbox[0].reply_to, ["sender@example.com"])

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

        # django-ratelimit uses fixed windows. Freeze its clock so this test
        # cannot cross a window boundary between POST requests.
        with patch("django_ratelimit.core.time.time", return_value=1_700_000_000):
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

    def test_home_page_no_user_with_email(self):
        # Clear users
        User.objects.all().delete()
        # Should raise 404
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    @override_settings(CONTACT_EMAIL=None)
    def test_home_page_missing_email_env_var(self):
        with self.assertRaises(ImproperlyConfigured):
            self.client.get(self.url)

    def test_get_cached_home_data_unmocked(self):
        """Test the real DB query within the unmocked get_home_data."""
        cache.clear()

        # Call the real unmocked function
        skills, works = _get_cached_home_data(self.test_email)

        # Assert data correctly fetched from DB
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].skill, "Python")
        self.assertEqual(len(works), 1)
        self.assertEqual(works[0].customer, "Test Customer")

        # Test the 404 behavior for non-existent email
        cache.clear()
        from django.http import Http404

        with self.assertRaises(Http404):
            _get_cached_home_data("nonexistent@example.com")

    def test_get_cached_home_data(self):
        cache.clear()

        with patch("base.views.get_object_or_404") as mock_get_404:
            mock_get_404.return_value = self.user

            with patch("base.views.User.objects.prefetch_related") as mock_prefetch:
                mock_qs = MagicMock()
                mock_prefetch.return_value = mock_qs

                # 1. Cache Miss
                skills, works = _get_cached_home_data(self.test_email)

                mock_prefetch.assert_called_once_with("skill_set", "work_set")
                mock_get_404.assert_called_once_with(mock_qs, email=self.test_email)

                self.assertEqual(len(skills), 1)
                self.assertEqual(skills[0].skill, "Python")
                self.assertEqual(len(works), 1)
                self.assertEqual(works[0].customer, "Test Customer")

                # Reset mocks
                mock_prefetch.reset_mock()
                mock_get_404.reset_mock()

                # 2. Cache Hit
                skills2, works2 = _get_cached_home_data(self.test_email)

                mock_prefetch.assert_not_called()
                mock_get_404.assert_not_called()

                self.assertEqual(skills, skills2)
                self.assertEqual(works, works2)
