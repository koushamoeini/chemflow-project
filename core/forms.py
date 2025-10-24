from django import forms
from django.contrib.auth import authenticate

class ConfirmPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "class": "form-control"}),
        label="رمز عبور",
        error_messages={'required': 'وارد کردن رمز عبور الزامی است.'}
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get("password")
        if pwd:
            if not self.user.is_authenticated or not authenticate(username=self.user.username, password=pwd):
                raise forms.ValidationError("رمز عبور اشتباه است.")
        
        return cleaned
