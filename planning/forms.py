from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import ProductionRequest, ProductionItem

# --------------- ۱. کلاس پایه سفارشی برای FormSet ----------------
class BaseProductionItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        
        # حذف فرم‌هایی که کاملاً خالی هستند و نباید ذخیره شوند
        # (این کار را جنگو معمولا انجام می‌دهد، اما برای اعتبارسنجی نیاز به شمارش داریم)
        non_empty_forms = 0
        for form in self.forms:
            # اگر فرم برای حذف علامت‌گذاری شده باشد، آن را نادیده بگیر
            if self.can_delete and form.cleaned_data.get('DELETE'):
                continue
            
            # بررسی کنید آیا فیلدهای کلیدی سطر پر شده‌اند یا نه
            product_name = form.cleaned_data.get('product_name')
            quantity = form.cleaned_data.get('quantity')
            
            if product_name and quantity:
                 non_empty_forms += 1
            
        # اطمینان از اینکه حداقل تعداد مورد نیاز (min_num) پر شده باشد
        # min_num=1 تنظیم شده، پس باید حداقل 1 فرم غیر خالی وجود داشته باشد.
        if non_empty_forms < self.min_num:
             # این خطا به دلیل وجود min_num=1 در factory ایجاد می‌شود، 
             # اما این کد سفارشی مطمئن می‌شود که اگر کاربر سطر اول را خالی بگذارد،
             # خطای واضح‌تری نمایش داده شود (اگرچه جنگو خودش خطا می‌دهد).
             raise forms.ValidationError("لطفاً حداقل یک ردیف محصول را به طور کامل پر کنید.")


# --------------- ۲. تعریف فرم‌ها ----------------
class ProductionRequestForm(forms.ModelForm):
    class Meta:
        model = ProductionRequest
        fields = []

class ProductionItemForm(forms.ModelForm):
    class Meta:
        model = ProductionItem
        fields = [
            "product_name",
            "quantity",
            "unit",
            "packaging_type",
            "customer_name",
            "description",
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام محصول'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1.00',
                'step': '0.01',
                'style': 'padding-left: 1rem;'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select'
            }),
            'packaging_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام مشتری'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 1
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ۱. حذف گزینه خالی (---------) از Select Box ها
        for name in ("packaging_type", "unit"):
            # اگر این فیلد یک فیلد از نوع انتخاب (ChoiceField/CharField with choices) باشد
            if isinstance(self.fields[name], forms.ChoiceField):
                # تنظیم empty_label به None باعث حذف گزینه پیش‌فرض خالی می‌شود.
                self.fields[name].empty_label = None 
        
        if not self.instance.pk:
            self.fields["quantity"].initial = None
            self.fields["packaging_type"].initial = None
            self.fields["unit"].initial = None
            
ProductionItemFormSet = inlineformset_factory(
    parent_model=ProductionRequest,
    model=ProductionItem,
    form=ProductionItemForm,
    formset=BaseProductionItemFormSet, # <--- استفاده از کلاس پایه سفارشی
    extra=1,                           # <--- کاهش تعداد سطرها به 2 (1 اجباری + 1 اضافی)
    can_delete=True,
    min_num=1,                         # <--- حفظ حداقل یک سطر اجباری
    validate_min=True,
)