from django.test import SimpleTestCase

from base.forms import ContactForm


class TestContactForm(SimpleTestCase):
    def test_contact_form_valid_data(self):
        form = ContactForm(
            data={
                "name": "John Doe",
                "subject": "Test Subject",
                "email": "johndoe@example.com",
                "body": "This is a test message.",
                "website": "https://example.com",
            }
        )
        self.assertTrue(form.is_valid())

    def test_contact_form_no_data(self):
        form = ContactForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 4)  # name, subject, email, body

    def test_contact_form_missing_required_fields(self):
        form = ContactForm(data={"name": "John Doe"})
        self.assertFalse(form.is_valid())
        self.assertIn("subject", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("body", form.errors)

    def test_contact_form_invalid_email(self):
        form = ContactForm(
            data={
                "name": "John Doe",
                "subject": "Test Subject",
                "email": "not-an-email",
                "body": "This is a test message.",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_contact_form_max_length_exceeded(self):
        form = ContactForm(
            data={
                "name": "a" * 256,
                "subject": "b" * 256,
                "email": "johndoe@example.com",
                "body": "This is a test message.",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("subject", form.errors)

    def test_contact_form_website_optional(self):
        form = ContactForm(
            data={
                "name": "John Doe",
                "subject": "Test Subject",
                "email": "johndoe@example.com",
                "body": "This is a test message.",
                "website": "",
            }
        )
        self.assertTrue(form.is_valid())
