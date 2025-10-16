from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

class Product(models.Model):
    code = models.CharField(
        max_length=50, 
        verbose_name="کد محصول",
        unique=True
    )
    name = models.CharField(max_length=200, verbose_name="نام محصول")
    
    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Customer(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام مشتری")
    phone = models.CharField(max_length=50, verbose_name="شماره تماس مشتری")
    address = models.TextField(verbose_name="آدرس")
    customer_code = models.CharField(
        max_length=50, 
        verbose_name="کد مشتری",
        unique=True,    
        blank=False,    
        null=False      
    )
    
    class Meta:
        verbose_name = "مشتری"
        verbose_name_plural = "مشتریان"
    
    def __str__(self):
        return f"{self.customer_code} - {self.name}"
    
    
class OfficialTypeChoices(models.TextChoices):
    OFFICIAL = "official", _("رسمی")
    INFORMAL = "informal", _("غیر رسمی")


class RequestType(models.Model):
    name = models.CharField(max_length=100, verbose_name="نوع درخواست")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    display_order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")
    
    class Meta:
        verbose_name = "نوع درخواست"
        verbose_name_plural = "انواع درخواست"
        ordering = ["display_order", "name"]
    
    def __str__(self):
        return self.name


class PackagingType(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام نوع بسته‌بندی")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    display_order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")
    
    class Meta:
        verbose_name = "نوع بسته‌بندی"
        verbose_name_plural = "انواع بسته‌بندی"
        ordering = ["display_order", "name"]
    
    def __str__(self):
        return self.name


class Unit(models.Model):
    name = models.CharField(max_length=100, verbose_name="واحد اندازه‌گیری")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    display_order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")
    
    class Meta:
        verbose_name = "واحد"
        verbose_name_plural = "واحد اندازه گیری"
        ordering = ["display_order", "name"]
    
    def __str__(self):
        return self.name


class ShippingMethod(models.Model):
    name = models.CharField(max_length=100, verbose_name="روش ارسال")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    display_order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")
    
    class Meta:
        verbose_name = "روش ارسال"
        verbose_name_plural = "روش‌های ارسال"
        ordering = ["display_order", "name"]
    
    def __str__(self):
        return self.name


class OrderStatus(models.TextChoices):
    DRAFT = "draft", _("پیش‌نویس")
    SALES_APPROVED = "sales_approved", _("تایید فروش")
    FINANCE_APPROVED = "finance_approved", _("تایید مالی")
    MANAGEMENT_APPROVED = "management_approved", _("تایید مدیریت")
    CANCELED = "canceled", _("لغو شده")

class CustomerOrder(models.Model):
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="orders_created")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=32, choices=OrderStatus.choices, default=OrderStatus.DRAFT)
    order_date = models.DateField(auto_now_add=True)
    order_number = models.CharField(max_length=20, unique=True, editable=False)

    official_type = models.CharField(max_length=10, choices=OfficialTypeChoices.choices,
                                     default=OfficialTypeChoices.OFFICIAL, verbose_name="نوع رسمیت")
    request_type = models.ForeignKey(
        RequestType,
        on_delete=models.PROTECT,
        verbose_name="نوع درخواست"
    )
    customer_code = models.CharField(
        max_length=50, 
        verbose_name="کد مشتری",
        blank=True,
        null=True
    )
    customer_name = models.CharField(max_length=200, verbose_name="نام مشتری")
    customer_phone = models.CharField(
        max_length=50, verbose_name="شماره تماس مشتری")
    recipient_address = models.TextField(verbose_name="آدرس گیرنده")
    order_notes = models.TextField(
        blank=True, verbose_name="توضیحات کلی سفارش")

    canceled_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders_canceled")
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(blank=True)

    sales_approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders_sales_approved")
    sales_approved_at = models.DateTimeField(null=True, blank=True)

    finance_approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders_finance_approved")
    finance_approved_at = models.DateTimeField(null=True, blank=True)

    management_approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders_management_approved")
    management_approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_number} - {self.customer_name}"

    def _generate_order_number(self):
        now = timezone.now()
        prefix = f"ORD-{now.strftime('%Y%m')}-"
        with transaction.atomic():
            last = (CustomerOrder.objects
                    .select_for_update(skip_locked=True)
                    .filter(order_number__startswith=prefix)
                    .order_by("-order_number")
                    .first())
            last_seq = int(last.order_number.split("-")[-1]) if last else 0
            return f"{prefix}{last_seq + 1:04d}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def is_editable(self, user):
        if not user.is_authenticated or not hasattr(user, 'profile'):
            return False

        if self.status == OrderStatus.CANCELED:
            return False

        role = user.profile.user_type

        if role == 'management':
            return True

        if role == 'sales_manager':
            return self.status in [OrderStatus.DRAFT, OrderStatus.SALES_APPROVED]

        if role == 'finance_manager':
            return self.status in [OrderStatus.SALES_APPROVED, OrderStatus.FINANCE_APPROVED]

        return False
    def can_approve_sales(self, user):
        return (hasattr(user, "profile")
                and user.profile.user_type in ["management", "sales_manager"]
                and self.status == OrderStatus.DRAFT)

    def can_approve_finance(self, user):
        return (hasattr(user, "profile")
                and user.profile.user_type in ["management", "finance_manager"]
                and self.status == OrderStatus.SALES_APPROVED)

    def can_approve_management(self, user):
        return (hasattr(user, "profile")
                and user.profile.user_type == "management"
                and self.status == OrderStatus.FINANCE_APPROVED)

    def can_cancel(self, user):
        if not user.is_authenticated or not hasattr(user, "profile"):
            return False

        if self.status == OrderStatus.CANCELED:
            return False

        role = user.profile.user_type

        if role == "management":
            return True

        if role == "sales_manager":
            return self.created_by_id == user.id and self.status in [OrderStatus.DRAFT, OrderStatus.SALES_APPROVED]

        if role == "finance":
            return self.status in [OrderStatus.SALES_APPROVED, OrderStatus.FINANCE_APPROVED]

        return False


class OrderItem(models.Model):
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        verbose_name="محصول",
        null=True,
        blank=True
    )
    product_code = models.CharField(max_length=50, verbose_name="کد محصول",blank=True,null=True)
    product_name = models.CharField(max_length=200, verbose_name="نام محصول")
    packaging_type = models.ForeignKey(
        PackagingType, 
        on_delete=models.PROTECT, 
        verbose_name="نوع بسته‌بندی"
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.00"), verbose_name="مقدار")
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        verbose_name="واحد"
    )
    batch_number = models.CharField(max_length=100, blank=True, verbose_name="شماره بچ")
    shipping_method = models.ForeignKey(
        ShippingMethod,
        on_delete=models.PROTECT,
        verbose_name="روش ارسال"
    )
    description = models.CharField(max_length=500, blank=True, verbose_name="توضیحات")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.product_name} × {self.quantity} {self.unit}"
