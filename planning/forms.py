from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import ProductionRequest, ProductionItem

class BaseProductionItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        
        valid_forms_count = 0
        deleted_forms_count = 0
        
        for form in self.forms:
            if self.can_delete and form.cleaned_data.get('DELETE'):
                deleted_forms_count += 1
                continue
            
            if form.is_valid() and form.has_changed():
                valid_forms_count += 1



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
            'unit': {'required': "این فیلد لازم هست"},
            'packaging_type': {'required': "این فیلد لازم هست"},
            'product_name': {'required': "این فیلد لازم هست"},
            'quantity': {'required': "این فیلد لازم هست"},
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['unit'].empty_label = ""
        self.fields['packaging_type'].empty_label = ""

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
    min_num=1,
    validate_min=True,
)