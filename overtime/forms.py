from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import OvertimeRequest, OvertimeItem, Department

class BaseOvertimeItemFormSet(BaseInlineFormSet):
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
                raise forms.ValidationError("لطفاً حداقل اطلاعات یک ردیف پرسنل را پر کنید.")

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