

from rest_framework import permissions

class UserPermission(permissions.BasePermission):
    """
    Comprehensive permission class:
    - Anyone can create an account
    - Users can view/update only their own account
    - Superusers have full access
    """

    def has_permission(self, request, view):
        # Always allow account creation
        if view.action == 'create':
            return True
        
        # Require authentication for other actions
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers can perform all actions
        if request.user.is_superuser:
            return True
        
        # Allow specific actions for authenticated users
        allowed_actions = ['retrieve', 'update', 'partial_update', 'destroy', 'profile', 'change_password']
        return view.action in allowed_actions

    def has_object_permission(self, request, view, obj):
        # Superusers have full access
        if request.user.is_superuser:
            return True
        
        # Users can only access their own account
        return obj == request.user
