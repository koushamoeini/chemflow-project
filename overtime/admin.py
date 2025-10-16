from django.contrib import admin
from .models import Department, OvertimeRequest, OvertimeItem

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(OvertimeRequest)
class OvertimeRequestAdmin(admin.ModelAdmin):
    list_display = ['request_number', 'created_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['request_number', 'created_by__username']
    readonly_fields = ['request_number', 'created_at']

@admin.register(OvertimeItem)
class OvertimeItemAdmin(admin.ModelAdmin):
    list_display = ['employee_name', 'department', 'start_time', 'end_time', 'overtime_request']
    list_filter = ['department']
    search_fields = ['employee_name', 'overtime_request__request_number']
