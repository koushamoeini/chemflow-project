from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import ProductionRequest, ProductionItem

class BaseProductionItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        
        non_empty_forms = 0
        for form in self.forms:
            if self.can_delete and form.cleaned_data.get('DELETE'):
                continue
            
            product_name = form.cleaned_data.get('product_name')
            quantity = form.cleaned_data.get('quantity')
            
            if product_name and quantity:
                non_empty_forms += 1
        
        if non_empty_forms < self.min_num:
            raise forms.ValidationError("لطفاً حداقل یک ردیف محصول را به طور کامل پر کنید.")

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
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'توضیحات'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance.pk:
            self.fields["quantity"].initial = None
            
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

