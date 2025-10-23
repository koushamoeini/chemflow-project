from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import ProductionRequest, ProductionItem

class BaseProductionItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        num_valid_forms = 0
        num_forms_submitted = 0
        num_non_deleted_forms = 0

        for i, form in enumerate(self.forms):
            if self.can_delete and form.cleaned_data.get('DELETE'):
                continue

            num_non_deleted_forms += 1

            if form.has_changed():
                num_forms_submitted += 1
                if not form.errors: 
                    num_valid_forms += 1
        
        if num_non_deleted_forms == 0 and len(self.forms) > 0 :
            pass 
        elif num_forms_submitted == 0 and num_non_deleted_forms > 0:
            raise forms.ValidationError(
                "لطفاً حداقل اطلاعات یک ردیف محصول را پر کنید.", code='no_forms_submitted'
            )
        
        elif num_forms_submitted > 0 and num_valid_forms == 0:
            pass


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
                'placeholder': 'توضیحات',
                'rows': 1 
            }),
        }
        error_messages = {
            'unit': {'required': "این فیلد الزامی هست"},
            'packaging_type': {'required': "این فیلد الزامی هست"},
            'product_name': {'required': "این فیلد الزامی هست"},
            'quantity': {'required': "این فیلد الزامی هست"},
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['unit'].empty_label = "واحد را انتخاب کنید"
        self.fields['packaging_type'].empty_label = "بسته‌بندی را انتخاب کنید"

        if not self.instance.pk:
            self.fields["quantity"].initial = None
            
        if self.errors:
            for field_name in self.errors:
                if field_name in self.fields:
                    widget_class = self.fields[field_name].widget.attrs.get('class', '')
                    if 'is-invalid' not in widget_class:
                        self.fields[field_name].widget.attrs['class'] = widget_class + ' is-invalid'
            
ProductionItemFormSet = inlineformset_factory(
    parent_model=ProductionRequest,
    model=ProductionItem,
    form=ProductionItemForm,
    formset=BaseProductionItemFormSet, 
    extra=0, 
    can_delete=True,
    min_num=0, 
    validate_min=False, 
)

