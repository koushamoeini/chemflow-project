from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import CostCenter, Request, RequestItem, RequestType

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = []

class BaseRequestItemFormSet(BaseInlineFormSet):
    
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
        
        # --- این همان منطق جدیدی است که درخواست کردی ---
        has_at_least_one_item = any(f.has_changed() for f in non_deleted_forms)
        is_creating_new = not (self.instance and self.instance.pk)
        
        is_updating_and_deleting_all = False
        if not is_creating_new:
            if not non_deleted_forms and self.initial_forms:
                 is_updating_and_deleting_all = True

        if not has_at_least_one_item and not is_updating_and_deleting_all:
            if is_creating_new:
                raise forms.ValidationError("لطفاً حداقل اطلاعات یک ردیف آیتم را پر کنید.")
        # --- پایان منطق جدید ---


class RequestItemForm(forms.ModelForm):
    class Meta:
        model = RequestItem
        fields = ['request_type', 'cost_center', 'description']
        widgets = {
            'request_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 1
            }),
        }
        error_messages = {
            'request_type': {
                'required': "انتخاب نوع درخواست الزامی است.",
            },
            'cost_center': {
                'required': "انتخاب مرکز هزینه الزامی است.",
            },
            'description': {
                'required': "وارد کردن توضیحات الزامی است.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['request_type'].queryset = RequestType.objects.filter(is_active=True)
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)

        self.fields['request_type'].empty_label = "انتخاب کنید"
        self.fields['cost_center'].empty_label = "انتخاب کنید"
        self.fields['description'].required = True

        if self.errors:
           for field_name in self.errors:
               if field_name in self.fields:
                   widget_class = self.fields[field_name].widget.attrs.get('class', '')
                   if 'is-invalid' not in widget_class:
                       self.fields[field_name].widget.attrs['class'] = widget_class + ' is-invalid'


RequestItemFormSet = inlineformset_factory(
    parent_model=Request,
    model=RequestItem,
    form=RequestItemForm,
    formset=BaseRequestItemFormSet,
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=False
)