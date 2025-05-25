from django import forms
from .models import Person
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password


phone_number_validator = RegexValidator(
    regex=r'^\d{10}$',
    message='Please enter a valid 10-digit phone number.',
)


class PersonForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    phone_number = forms.CharField(
        validators=[phone_number_validator],
    )

    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'email', 'gender', 'phone_number']
        exclude = ['gender']
        widgets = {
            'first_name': forms.TextInput(attrs={'required': True}),
            'last_name': forms.TextInput(attrs={'required': True}),
            'email': forms.EmailInput(attrs={'required': True}),
            'phone_number': forms.TextInput(attrs={'required': True}),

        }

    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.initial['is_active'] = False

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            validate_password(password)
        except ValidationError as e:
            # This will add the validation error to the password field
            self.add_error('password', e)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            self.add_error(
                'password', "Error! Password and Confirm Password does not match")
        return cleaned_data


    def save(self, commit=True):
        self.instance.username = self.cleaned_data['email']
        return super().save(commit)


class ProfileSetting(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    phone_number = forms.CharField()

    class Meta:
        model = Person
        fields = ['first_name', 'last_name',
                  'email', 'password', 'confirm_password']


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'required': True,
        }
    ))
    new_password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'required': True,
        }
    ))
    confirm_password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'required': True,
        }
    ))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')

        if self.user and not self.user.check_password(current_password):
            raise ValidationError("Invalid current password.")

        return current_password

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        try:
            validate_password(new_password)
        except ValidationError as e:
            # This will add the validation error to the password field
            self.add_error('new_password', e)
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error(
                'confirm_password', "Error! New Password and Confirm Password does not match")

        return cleaned_data


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class PasswordResttingForm(PasswordResetForm):
    email = forms.CharField(max_length=254,
                            widget=forms.EmailInput(
                                attrs={
                                    "class": "text-box form-control email_validation",
                                    'required': True,
                                    'placeholder': "Email address",
                                }
                            )
                            )

    class Meta:
        fields = ('email')


class ForgotPasswordSetForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "input100 field-input",
                "placeholder": "New Password",
                "type": 'password',
                "id": "id_password1",
            }
        )
    )

    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "input100 field-input",
                "placeholder": "Confirm Password",
                "type": 'password',
                "id": "id_password2"
            }
        )
    )

    class Meta:
        fields = ('new_password1', 'new_password2')
