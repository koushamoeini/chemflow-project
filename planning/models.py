from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from orders.models import PackagingType, Unit

class ProductionStatus(models.TextChoices):
    DRAFT = "draft", _("پیش‌نویس")
    PLANNING_SIGNED = "planning_signed", _("تأیید برنامه‌ریزی")
    FACTORY_SIGNED  = "factory_signed",  _("تأیید کارخانه")
    CANCELED = "canceled", _("لغو شده")

class ProductionRequest(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="prodreq_created")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, choices=ProductionStatus.choices, default=ProductionStatus.DRAFT)

    request_date = models.DateField(auto_now_add=True)
    request_number = models.CharField(max_length=20, unique=True, editable=False) 

    # approvals
    planning_signed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="prodreq_planning_signed")
    planning_signed_at = models.DateTimeField(null=True, blank=True)

    factory_signed_by  = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="prodreq_factory_signed")
    factory_signed_at  = models.DateTimeField(null=True, blank=True)

    canceled_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="prodreq_canceled")
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.request_number}"

    def _generate_request_number(self):
        # ... (منطق تولید شماره درخواست حفظ شد) ...
        now = timezone.now()
        prefix = f"PR-{now.strftime('%Y%m')}-"
        with transaction.atomic():
            last = (ProductionRequest.objects
                    .select_for_update(skip_locked=True)
                    .filter(request_number__startswith=prefix)
                    .order_by("-request_number")
                    .first())
            last_seq = int(last.request_number.split("-")[-1]) if last else 0
            return f"{prefix}{last_seq + 1:04d}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            self.request_number = self._generate_request_number()
        super().save(*args, **kwargs)

    # ... (متدهای can_edit_by, can_sign_planning, can_sign_factory, can_cancel حفظ شد) ...
    def can_edit_by(self, user):
        if not getattr(user, "is_authenticated", False) or not hasattr(user, "profile"):
            return False
        role = user.profile.user_type
        if role in ["management", "factory_manager"]:
            return True
        if role == "factory_planner":
            return self.status in [ProductionStatus.DRAFT, ProductionStatus.PLANNING_SIGNED] and self.created_by_id == user.id
        return False

    def can_sign_planning(self, user):
        return hasattr(user, "profile") and user.profile.user_type in ["factory_planner", "management"] and self.status == ProductionStatus.DRAFT

    def can_sign_factory(self, user):
        return hasattr(user, "profile") and user.profile.user_type in ["factory_manager", "management"] and self.status == ProductionStatus.PLANNING_SIGNED

    def can_cancel(self, user):
        if not getattr(user, "is_authenticated", False) or not hasattr(user, "profile"):
            return False
        role = user.profile.user_type
        if self.status == ProductionStatus.CANCELED:
            return False
        if role == "management":
            return True
        if role == "factory_planner":
            return self.created_by_id == user.id and self.status in [ProductionStatus.DRAFT, ProductionStatus.PLANNING_SIGNED]
        return False


class ProductionItem(models.Model):
    request = models.ForeignKey(ProductionRequest, on_delete=models.CASCADE, related_name="items")

    # فیلدها برای امکان خالی بودن در سطر دوم، blank=True شدند.
    product_name = models.CharField(max_length=200, verbose_name="نام محصول", blank=True)
    packaging_type = models.ForeignKey(
        PackagingType,
        on_delete=models.PROTECT,
        verbose_name="نوع بسته‌بندی",
        blank=True,
        null=True
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("1.000"), verbose_name="مقدار", null=True, blank=True) # null=True هم برای DecimalField نیاز است
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        verbose_name="واحد", 
        blank=True,
        null=True
    )
    customer_name = models.CharField(max_length=200, verbose_name="نام مشتری", blank=True)
    description = models.TextField(blank=True, verbose_name="توضیحات") # این فیلد قبلا blank=True بود.

    def __str__(self):
        return self.product_name

class PlanningStatus(models.Model):
    # ... (کلاس PlanningStatus حفظ شد) ...
    order = models.OneToOneField(
        'orders.CustomerOrder', 
        on_delete=models.CASCADE,
        related_name='planning_status'
    )
    is_planned = models.BooleanField(default=False)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Planning Statuses"

    def __str__(self):
        return f"{self.order.order_number} - {'✅ Planned' if self.is_planned else '🟡 Ready'}"