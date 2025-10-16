# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.views import LoginView, LogoutView
from .forms import RegistrationForm
from .models import Profile


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"

    # Optional: keep users from being redirected to /admin unless staff
    def get_success_url(self):
        user = self.request.user
        next_url = self.get_redirect_url()  # ?next=...
        if next_url:
            if not user.is_staff and next_url.startswith("/admin"):
                return reverse("core:dashboard")
            return next_url
        return reverse("core:dashboard")  # default after login


class CustomLogoutView(LogoutView):
    # No special template needed; redirect is handled by LOGOUT_REDIRECT_URL
    pass


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # require admin approval
            user.save()

            Profile.objects.create(
                user=user,
                user_type=form.cleaned_data.get("user_type")
            )

            messages.success(
                request, "حساب کاربری شما ایجاد شد و منتظر تأیید مدیر است.")
            return redirect("accounts:login")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})
