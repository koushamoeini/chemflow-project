from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserType


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False, label="ایمیل (اختیاری)")

    user_type = forms.ChoiceField(
        label="نوع کاربر",
        choices=UserType.choices,
        widget=forms.RadioSelect(attrs={'class': 'radio-row'}), 
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = ''

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "user_type",
        ]
        labels = {
            "username": "نام کاربری",
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "password1": "رمز عبور",
            "password2": "تکرار رمز عبور",
        }
