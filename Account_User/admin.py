# Account_User/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from maintenance_company.models import MaintenanceCompanyProfile
from technician.models import TechnicianProfile
from developer.models import DeveloperProfile
from Account_User.models import User

class BaseProfileInline(admin.StackedInline):
    extra = 1
    can_delete = False

class TechnicianProfileInline(BaseProfileInline):
    model = TechnicianProfile

class MaintenanceProfileInline(BaseProfileInline):
    model = MaintenanceCompanyProfile
    fk_name = 'user'  # Specify the OneToOneField linking to User

class DeveloperProfileInline(BaseProfileInline):
    model = DeveloperProfile

class CustomUserAdmin(UserAdmin):
    inlines = [
        TechnicianProfileInline,
        MaintenanceProfileInline,
        DeveloperProfileInline
    ]
    list_display = (
        'email', 'first_name', 'last_name', 
        'account_type', 'is_staff', 'is_active'
    )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'account_type')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'phone_number', 'first_name', 'last_name', 
                'account_type', 'password1', 'password2', 
                'is_staff', 'is_active'
            )
        }),
    )
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(TechnicianProfile)
admin.site.register(MaintenanceCompanyProfile)
admin.site.register(DeveloperProfile)

