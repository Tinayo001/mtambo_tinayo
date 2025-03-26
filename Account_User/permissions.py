from rest_framework import permissions

class UserPermission(permissions.BasePermission):
    """
    Custom permission to:
    - Allow anyone to create an account
    - Allow owners to update/edit/destroy/read their own profile
    - Allow admins to view all profiles
    """
    def has_permission(self, request, view):
        # Always allow account creation
        if view.action == 'create':
            return True
        
        # Require authentication for other actions
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow admins to list all users
        if view.action == 'list':
            return request.user.is_staff or request.user.is_superuser
        
        return True

    def has_object_permission(self, request, view, obj):
        # Allow full access to admins and superusers
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Allow users to access/modify/destroy only their own profile
        # This applies to retrieve, update, partial_update, and destroy actions
        return obj == request.user