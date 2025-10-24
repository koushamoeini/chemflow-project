from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.contrib.auth import authenticate
from .models import CustomerOrder,OrderItem, PackagingType, RequestType, ShippingMethod, Unit


class BaseOrderItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if not hasattr(self, '_errors'):
            return

        new_errors_list = []
        non_deleted_forms = []

        for i, form in enumerate(self.forms):
            delete_field_name = f'{form.prefix}-DELETE'
            is_marked_for_delete = self.data.get(delete_field_name) in ('on', 'True', 'true', '1')

            if is_marked_for_delete:
                new_errors_list.append({}) 
                form.cleaned_data = {'DELETE': True} 
            else:
                non_deleted_forms.append(form)
                if i < len(self._errors):
                    new_errors_list.append(self._errors[i])
                else:
                    new_errors_list.append({}) 

        self._errors = new_errors_list
        
        if any(self.errors):
            return
        
        has_at_least_one_item = any(f.has_changed() for f in non_deleted_forms)
        is_creating_new = not (self.instance and self.instance.pk)
        
        is_updating_and_deleting_all = False
        if not is_creating_new:
            if not non_deleted_forms and self.initial_forms:
                 is_updating_and_deleting_all = True

        if not has_at_least_one_item and not is_updating_and_deleting_all:
            if is_creating_new:
                raise forms.ValidationError("لطفاً حداقل اطلاعات یک ردیف محصول را پر کنید.")


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
        error_messages = {
            'product_name': {'required': "این فیلد الزامی هست"},
            'quantity': {'required': "این فیلد الزامی هست"},
            'unit': {'required': "این فیلد الزامی هست"},
            'packaging_type': {'required': "این فیلد الزامی هست"},
            'shipping_method': {'required': "این فیلد الزامی هست"},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['packaging_type'].queryset = PackagingType.objects.filter(is_active=True)
        self.fields['unit'].queryset = Unit.objects.filter(is_active=True)
        self.fields['shipping_method'].queryset = ShippingMethod.objects.filter(is_active=True)
        
        self.fields['packaging_type'].empty_label = "انتخاب کنید"
        self.fields['unit'].empty_label = "انتخاب کنید"
        self.fields['shipping_method'].empty_label = "انتخاب کنید"

        if 'DELETE' in self.fields:
            self.fields['DELETE'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
            self.fields['DELETE'].label = False
            
        if self.errors:
            for field_name in self.errors:
                if field_name in self.fields:
                    widget_class = self.fields[field_name].widget.attrs.get('class', '')
                    if 'is-invalid' not in widget_class:
                        self.fields[field_name].widget.attrs['class'] = widget_class + ' is-invalid'


OrderItemFormSet = inlineformset_factory(
    parent_model=CustomerOrder,
    model=OrderItem,
    form=OrderItemForm,
    formset=BaseOrderItemFormSet,
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=False,
)