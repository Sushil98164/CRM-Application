from django import forms
from django.core.validators import EmailValidator
from .models import Contact
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

class ContactForm(forms.ModelForm):
    email = forms.EmailField(validators=[EmailValidator(message="Please enter a valid email address.")], required=True)
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'required': True}),
            'subject': forms.TextInput(attrs={'required': True}),
            'message': forms.Textarea(attrs={'required': True}),
        }

    def clean_captcha(self):
        captcha = self.cleaned_data.get('captcha')
        if not captcha:
            self.add_error('captcha', 'Captcha is required')
        return captcha
