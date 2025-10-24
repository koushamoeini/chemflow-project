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

        num_valid_forms = 0
        num_forms_submitted = 0
        num_non_deleted_forms = 0

        for i, form in enumerate(self.forms):
            if self.can_delete and form.cleaned_data.get('DELETE'):
                continue

            num_non_deleted_forms += 1

            if form.has_changed():
                 num_forms_submitted += 1
                 if form.is_valid():
                    num_valid_forms += 1
            elif form.instance.pk and not form.errors:
                 num_valid_forms += 1
                 num_forms_submitted +=1

        if num_non_deleted_forms == 0 and len(self.forms) > 0 and self.min_num == 0:
             pass

        elif num_non_deleted_forms > 0 and num_forms_submitted == 0:
            if self.min_num > 0 or not any(f.instance.pk for f in self.forms):
                 raise forms.ValidationError(
                    "لطفاً حداقل اطلاعات یک ردیف آیتم را پر کنید.", code='no_forms_submitted'
                 )

        elif self.validate_min and num_non_deleted_forms < self.min_num:
             raise forms.ValidationError(
                 f"حداقل باید {self.min_num} آیتم وارد کنید.", code='min_num_required'
             )


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

