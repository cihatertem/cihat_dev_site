from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(max_length=255)
    subject = forms.CharField(max_length=255)
    email = forms.EmailField()
    body = forms.CharField(widget=forms.Textarea)
    website = forms.CharField(required=False)
