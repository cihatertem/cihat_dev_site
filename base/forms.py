from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(max_length=255)
    subject = forms.CharField(max_length=255)
    email = forms.EmailField()
    body = forms.CharField(widget=forms.Textarea)
    website = forms.CharField(required=False)

    def clean_name(self):
        name = self.cleaned_data.get("name", "")
        if "\n" in name or "\r" in name:
            raise forms.ValidationError("Name cannot contain newline characters.")
        return name

    def clean_subject(self):
        subject = self.cleaned_data.get("subject", "")
        if "\n" in subject or "\r" in subject:
            raise forms.ValidationError("Subject cannot contain newline characters.")
        return subject
