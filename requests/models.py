from django.db import models
from django.conf import settings

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

class CostCenter(models.Model):
    name = models.CharField(max_length=100, verbose_name="مرکز هزینه")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    display_order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")
    
    class Meta:
        verbose_name = "مرکز هزینه"
        verbose_name_plural = "مراکز هزینه"
        ordering = ["display_order", "name"]
    
    def __str__(self):
        return self.name

class RequestStatus(models.TextChoices):
    DRAFT = 'draft', 'پیش‌نویس'
    CREATOR_APPROVED = 'creator_approved', 'تایید درخواست‌کننده'
    FACTORY_APPROVED = 'factory_approved', 'تایید مدیر کارخانه'
    MANAGEMENT_APPROVED = 'management_approved', 'تایید مدیر اصلی'
    CANCELED = 'canceled', 'لغو شده'

class Request(models.Model):
    request_number = models.CharField(max_length=50, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='submitted_requests', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=RequestStatus.choices, default=RequestStatus.DRAFT)
    is_completed = models.BooleanField(default=False)
    canceled_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='canceled_requests', on_delete=models.SET_NULL, null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(blank=True, null=True)
    creator_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='approved_requests_creator', on_delete=models.SET_NULL, null=True, blank=True)
    creator_approved_at = models.DateTimeField(null=True, blank=True)
    factory_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='approved_requests_factory', on_delete=models.SET_NULL, null=True, blank=True)
    factory_approved_at = models.DateTimeField(null=True, blank=True)
    management_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='approved_requests_management', on_delete=models.SET_NULL, null=True, blank=True)
    management_approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.request_number

    def can_edit_by(self, user):
        user_type = getattr(user.profile, "user_type", None)

        if self.status == RequestStatus.CANCELED or self.is_completed:
            return False

        if user == self.created_by:
            return self.status in [RequestStatus.DRAFT, RequestStatus.CREATOR_APPROVED, RequestStatus.FACTORY_APPROVED]

        if user_type == "factory_manager":
            return self.status in [RequestStatus.CREATOR_APPROVED, RequestStatus.FACTORY_APPROVED]

        if user_type == "management":
            return True

        return False


    def can_cancel(self, user):
        return self.status not in [RequestStatus.CANCELED]

    def can_approve_creator(self, user):
        return user == self.created_by and self.status == RequestStatus.DRAFT

    def can_approve_factory(self, user):
        return user.profile.user_type == 'factory_manager' and self.status == RequestStatus.CREATOR_APPROVED

    def can_approve_management(self, user):
        return user.profile.user_type == 'management' and self.status == RequestStatus.FACTORY_APPROVED

class RequestItem(models.Model):
    request = models.ForeignKey(Request, related_name='items', on_delete=models.CASCADE)
    request_type = models.ForeignKey(RequestType,on_delete=models.PROTECT,verbose_name="نوع درخواست")
    cost_center = models.ForeignKey(CostCenter,on_delete=models.PROTECT,  verbose_name="مرکز هزینه")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Item for Request {self.request.request_number} ({self.request_type})"
