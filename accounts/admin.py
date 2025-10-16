from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0

class UserAdmin(DjangoUserAdmin):
    inlines = [ProfileInline]
    list_display = ("username", "first_name", "last_name", "email", "is_active", "is_staff")

# swap the default User admin to include our inline
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

