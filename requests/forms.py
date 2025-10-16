from django import forms
from django.forms import inlineformset_factory
from .models import CostCenter, Request, RequestItem, RequestType

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = []

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
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active items in dropdowns
        self.fields['request_type'].queryset = RequestType.objects.filter(is_active=True)
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)

RequestItemFormSet = inlineformset_factory(
    parent_model=Request,
    model=RequestItem,
    form=RequestItemForm,
    extra=1,
    can_delete=True
)