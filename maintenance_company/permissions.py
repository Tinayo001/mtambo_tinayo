from rest_framework import permissions
from maintenance_company.models import MaintenanceCompanyProfile

class IsSuperUser(permissions.BasePermission):
    """
    Permission to only allow superusers to access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsMaintenanceCompanyAdmin(permissions.BasePermission):
    """
    Permission to only allow maintenance company admins to access their companies.
    """
    def has_permission(self, request, view):
        return request.user and request.user.account_type == 'maintenance'

    def has_object_permission(self, request, view, obj):
        # Check if user is a maintenance company admin
        if not request.user.account_type == 'maintenance':
            return False
            
        # If object is MaintenanceCompanyProfile, check if user is admin
        if isinstance(obj, MaintenanceCompanyProfile):
            return obj.admin_user == request.user
            
        # If we're dealing with a detail action on a MaintenanceCompanyViewSet
        if hasattr(view, 'get_object') and view.basename == 'maintenance-company':
            try:
                # Get the company from the request
                company = view.get_object()
                # Check if the user is the admin of this company
                return company.admin_user == request.user
            except:
                return False
                
        return False


class IsAccountOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow users to edit their own accounts or admins of their maintenance company.
    """
    def has_object_permission(self, request, view, obj):
        # Allow if it's the user's own account
        if obj.id == request.user.id:
            return True
            
        # Allow if user is superuser
        if request.user.is_superuser:
            return True
            
        # Allow if user is maintenance company admin and obj is their technician
        if request.user.account_type == 'maintenance':
            try:
                admin_profile = MaintenanceCompanyProfile.objects.get(admin_user=request.user)
                
                # If obj is technician, check if they belong to admin's company
                if obj.account_type == 'technician' and hasattr(obj, 'technician_profile'):
                    return hasattr(obj.technician_profile, 'maintenance_company') and \
                           obj.technician_profile.maintenance_company == admin_profile
                           
            except MaintenanceCompanyProfile.DoesNotExist:
                return False
                
        return False


class IsOwnerOrSuperuser(permissions.BasePermission):
    """
    Permission to only allow owners of an object or superusers to view/edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Allow if user is superuser
        if request.user.is_superuser:
            return True
            
        # Allow if it's the user's own profile or account
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'id'):
            return obj.id == request.user.id
            
        return False