from functools import wraps
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import ConfirmPasswordForm

def require_password(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        # GET → show password page
        if request.method != "POST":
            form = ConfirmPasswordForm(request.user)
            return render(request, "confirm_password.html", {"form": form})
        # POST → validate password
        form = ConfirmPasswordForm(request.user, request.POST)
        if not form.is_valid():
            return render(request, "confirm_password.html", {"form": form})
        return view_func(request, *args, **kwargs)
    return _wrapped