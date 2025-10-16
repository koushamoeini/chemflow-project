from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import datetime
from django.db import transaction as db_transaction

class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام واحد/دپارتمان")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    display_order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        verbose_name = "واحد"
        verbose_name_plural = "واحدها"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

class OvertimeStatus(models.TextChoices):
    ADMIN_PENDING = "admin_pending", _("در انتظار مسئول اداری")
    FACTORY_PENDING = "factory_pending", _("در انتظار مدیر کارخانه")
    MANAGEMENT_PENDING = "management_pending", _("در انتظار مدیریت")
    APPROVED = "approved", _("تأیید شده")
    REJECTED = "rejected", _("رد شده")
    CANCELED = "canceled", _("لغو شده")

class OvertimeRequest(models.Model):
    request_number = models.CharField(max_length=50, unique=True, verbose_name="شماره درخواست")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="overtime_requests_created", verbose_name="ایجاد کننده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    status = models.CharField(max_length=20, choices=OvertimeStatus.choices, default=OvertimeStatus.ADMIN_PENDING, verbose_name="وضعیت")

    admin_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="overtime_requests_admin_approved", verbose_name="تأیید کننده مسئول اداری")
    admin_approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ تأیید مسئول اداری")
    
    factory_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="overtime_requests_factory_approved", verbose_name="تأیید کننده مدیر کارخانه")
    factory_approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ تأیید مدیر کارخانه")
    
    management_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="overtime_requests_management_approved", verbose_name="تأیید کننده مدیریت")
    management_approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ تأیید مدیریت")

    canceled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="overtime_requests_canceled", verbose_name="لغو کننده")
    canceled_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ لغو")
    cancel_reason = models.TextField(blank=True, verbose_name="دلیل لغو")

    class Meta:
        verbose_name = "درخواست اضافه کاری"
        verbose_name_plural = "درخواست‌های اضافه کاری"
        ordering = ["-created_at"]

    def __str__(self):
        return self.request_number

    def _generate_request_number(self):
        now = datetime.datetime.now()
        prefix = f"OT-{now.strftime('%Y%m')}-"
        with db_transaction.atomic():
            last = (OvertimeRequest.objects.select_for_update(skip_locked=True).filter(request_number__startswith=prefix).order_by("-request_number").first())
            last_seq = int(last.request_number.split("-")[-1]) if last else 0
            return f"{prefix}{last_seq + 1:04d}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            self.request_number = self._generate_request_number()
        super().save(*args, **kwargs)

    def can_approve_admin(self, user):
        if not hasattr(user, 'profile'): return False
        return (user.profile.user_type == 'administrative_officer' and self.status == OvertimeStatus.ADMIN_PENDING)

    def can_approve_factory(self, user):
        if not hasattr(user, 'profile'): return False
        return (user.profile.user_type == 'factory_manager' and self.status == OvertimeStatus.FACTORY_PENDING)

    def can_approve_management(self, user):
        if not hasattr(user, 'profile'): return False
        return (user.profile.user_type == 'management' and self.status == OvertimeStatus.MANAGEMENT_PENDING)

    def can_edit_or_cancel(self, user):
        if self.status in [OvertimeStatus.APPROVED, OvertimeStatus.REJECTED, OvertimeStatus.CANCELED]:
            return False

        if not hasattr(user, 'profile'):
            return False

        is_creator = (user == self.created_by)
        is_admin = (user.profile.user_type == 'administrative_officer')
        is_factory = (user.profile.user_type == 'factory_manager')
        is_management = (user.profile.user_type == 'management')

        if is_creator and not self.admin_approved_by:
            return True
        if is_admin and not self.factory_approved_by:
            return True
        if is_factory and not self.management_approved_by:
            return True
        if is_management:
            return True

        return False

    def get_next_approver(self):
        status_map = {
            OvertimeStatus.ADMIN_PENDING: 'مسئول اداری',
            OvertimeStatus.FACTORY_PENDING: 'مدیر کارخانه',
            OvertimeStatus.MANAGEMENT_PENDING: 'مدیریت',
            OvertimeStatus.APPROVED: 'تکمیل شده',
            OvertimeStatus.REJECTED: 'رد شده',
            OvertimeStatus.CANCELED: 'لغو شده',
        }
        return status_map.get(self.status, '—')

class OvertimeItem(models.Model):
    overtime_request = models.ForeignKey(OvertimeRequest, on_delete=models.CASCADE, related_name="items", verbose_name="درخواست اضافه کاری")
    employee_name = models.CharField(max_length=200, verbose_name="نام پرسنل")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, verbose_name="واحد")
    start_time = models.TimeField(verbose_name="ساعت شروع")
    end_time = models.TimeField(verbose_name="ساعت پایان")
    reason = models.TextField(verbose_name="علت اضافه کاری")

    class Meta:
        verbose_name = "آیتم اضافه کاری"
        verbose_name_plural = "آیتم‌های اضافه کاری"

    def __str__(self):
        return f"{self.employee_name} - {self.department.name}"

    @property
    def duration_minutes(self):
        if self.start_time and self.end_time:
            start_dt = datetime.datetime.combine(datetime.date.today(), self.start_time)
            end_dt = datetime.datetime.combine(datetime.date.today(), self.end_time)
            if end_dt < start_dt:
                end_dt += datetime.timedelta(days=1)
            duration = end_dt - start_dt
            return int(duration.total_seconds() / 60)
        return 0

    @property
    def duration_display(self):
        minutes = self.duration_minutes
        if minutes is not None:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours} ساعت و {mins} دقیقه"
        return "—"