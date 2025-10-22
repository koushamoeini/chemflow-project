from django import forms
from django.forms import inlineformset_factory
from .models import OvertimeRequest, OvertimeItem, Department

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
                'rows': 2,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)

OvertimeItemFormSet = inlineformset_factory(
    parent_model=OvertimeRequest,
    model=OvertimeItem, 
    form=OvertimeItemForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True
)