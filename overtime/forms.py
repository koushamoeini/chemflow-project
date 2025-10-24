from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import OvertimeRequest, OvertimeItem, Department

class BaseOvertimeItemFormSet(BaseInlineFormSet):
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
                "لطفاً حداقل اطلاعات یک ردیف پرسنل را پر کنید.", code='no_forms_submitted'
            )
        
        elif num_forms_submitted > 0 and num_valid_forms == 0:
            pass

class OvertimeRequestForm(forms.ModelForm):
    class Meta:
        model = OvertimeRequest
        fields = [] 

class OvertimeItemForm(forms.ModelForm):
    class Meta:
        model = OvertimeItem
        fields = ['employee_name', 'department', 'start_time', 'end_time', 'reason']
        widgets = {
            'employee_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام پرسنل را وارد کنید'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control', 
                'type': 'time'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 1,
                'placeholder': 'علت اضافه کاری را شرح دهید'
            }),
        }
        labels = {
            'employee_name': 'نام پرسنل',
            'department': 'واحد',
            'start_time': 'ساعت شروع',
            'end_time': 'ساعت پایان', 
            'reason': 'علت اضافه کاری'
        }
        error_messages = {
            'employee_name': {'required': "این فیلد الزامی هست"},
            'department': {'required': "این فیلد الزامی هست"},
            'start_time': {'required': "این فیلد الزامی هست"},
            'end_time': {'required': "این فیلد الزامی هست"},
            'reason': {'required': "این فیلد الزامی هست"},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].empty_label = "انتخاب کنید"

        if self.errors:
            for field_name in self.errors:
                if field_name in self.fields:
                    widget_class = self.fields[field_name].widget.attrs.get('class', '')
                    if 'is-invalid' not in widget_class:
                        self.fields[field_name].widget.attrs['class'] = widget_class + ' is-invalid'

OvertimeItemFormSet = inlineformset_factory(
    parent_model=OvertimeRequest,
    model=OvertimeItem, 
    form=OvertimeItemForm,
    formset=BaseOvertimeItemFormSet,
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=False
)
