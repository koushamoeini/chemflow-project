from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class UserType(models.TextChoices):
    MANAGEMENT = "management", _("مدیریت")
    SALES_MANAGER = "sales_manager", _("مدیر فروش")
    FINANCE_MANAGER = "finance_manager", _("مدیر مالی")
    FACTORY_PLANNER = "factory_planner", _("واحد برنامه‌ریزی")
    FACTORY_MANAGER = "factory_manager", _("مدیر کارخانه")
    ADMINISTRATIVE_OFFICER = "administrative_officer", _("مسئول اداری")

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    user_type = models.CharField(max_length=32, choices=UserType.choices, default=UserType.MANAGEMENT)

    def __str__(self):
        return f"{self.user.username} ({self.get_user_type_display()})"

