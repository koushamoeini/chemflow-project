from django.contrib import admin
from .models import RequestType, CostCenter

@admin.register(RequestType)
class RequestTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['name']