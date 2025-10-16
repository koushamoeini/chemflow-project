from django.contrib import admin
from .models import CustomerOrder, PackagingType, Customer, Product, RequestType, ShippingMethod, Unit  

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["customer_code", "name", "phone"]
    list_filter = ["name"]
    search_fields = ["customer_code", "name", "phone"]
    ordering = ["name"]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    search_fields = ["code", "name"]
    ordering = ["code"]

@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "order_date", "status", "created_by")
    list_filter = ("status", "order_date")
    search_fields = ("order_number", "customer_name", "product_name", "batch_number")
    readonly_fields = ("order_number", "order_date", "created_by",
                       "sales_approved_by", "sales_approved_at",
                       "finance_approved_by", "finance_approved_at",
                       "management_approved_by", "management_approved_at")
    
@admin.register(PackagingType)
class PackagingTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['name']
    
@admin.register(RequestType)
class RequestTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['name']    
    
@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['name']
    
    
@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['name']  