from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import ProductionRequest, ProductionItem

class BaseProductionItemFormSet(BaseInlineFormSet):
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