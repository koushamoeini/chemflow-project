from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth import authenticate
from .models import CustomerOrder,OrderItem, PackagingType, RequestType, ShippingMethod, Unit


class CustomerOrderForm(forms.ModelForm):
    class Meta:
        model = CustomerOrder
        fields = [
            "official_type",
            "request_type",
            "customer_code",
            "customer_name",
            "customer_phone",
            "recipient_address",
        ]
        labels = {
            "official_type": "نوع درخواست",
            "request_type": "نوع سفارش",
            "customer_code": "کد مشتری",
            "customer_name": "نام مشتری",
            "customer_phone": "شماره تماس مشتری",
            "recipient_address": "آدرس گیرنده",
        }
        widgets = {
            "official_type": forms.Select(attrs={"class": "form-select"}),
            "request_type": forms.Select(attrs={"class": "form-select"}),
            "customer_code": forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'کد مشتری را وارد کنید...'
            }),
            "customer_name": forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': ''
            }),
            "customer_phone": forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': ''
            }),
            
            "recipient_address": forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'آدرس کامل گیرنده را اینجا وارد کنید...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        
        # Make sure we only show active items in dropdowns
        
        self.fields['request_type'].queryset = RequestType.objects.filter(is_active=True)

        instance = getattr(self, "instance", None)
        user = getattr(self.request, "user", None)
        if instance and instance.pk:
            if not instance.is_editable(user):
                for f in self.fields.values():
                    f.disabled = True



class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = [
            "product_code",
            "product_name",
            "packaging_type",
            "quantity",
            "unit",
            "shipping_method",
            "batch_number",
            "description",
        ]
        labels = {
            "product_code": "کد محصول",
            "product_name": "نام محصول",
            "packaging_type": "نوع بسته‌بندی",
            "quantity": "مقدار",
            "unit": "واحد",
            "shipping_method": "روش ارسال",
            "batch_number": "شماره بچ",
            "description": "توضیحات",
        }
        widgets = {
              "product_code": forms.TextInput(attrs={ 
                'class': 'form-control',
            }),
            "product_name": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control ", "step": "0.01", "style": " padding-left: 1rem;"}),
            "packaging_type": forms.Select(attrs={"class": "form-select"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "shipping_method": forms.Select(attrs={"class": "form-select"}),
            "batch_number": forms.TextInput(attrs={"class": "form-control"}),
            'description': forms.Textarea(attrs={"class": "form-control", "rows": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make sure we only show active items in dropdowns
        self.fields['packaging_type'].queryset = PackagingType.objects.filter(is_active=True)
        self.fields['unit'].queryset = Unit.objects.filter(is_active=True)
        self.fields['shipping_method'].queryset = ShippingMethod.objects.filter(is_active=True)
        
        if 'DELETE' in self.fields:
            self.fields['DELETE'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
            self.fields['DELETE'].label = False


OrderItemFormSet = inlineformset_factory(
    parent_model=CustomerOrder,
    model=OrderItem,
    form=OrderItemForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)



class ConfirmPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "class": "form-control"})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get("password")
        if not self.user.is_authenticated or not authenticate(username=self.user.username, password=pwd):
            raise forms.ValidationError("رمز عبور اشتباه است.")
        return cleaned