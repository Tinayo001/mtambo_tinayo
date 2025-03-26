from rest_framework import permissions

class UserPermission(permissions.BasePermission):
    """
    Clear and simple permission class:
    - Anyone can create an account
    - Users can view, update, and delete ONLY their own account
    - Superusers can ONLY view ALL user accounts (no updates/deletes)
    """
    def has_permission(self, request, view):
        print(f"has_permission called - Action: {view.action}")
        print(f"User authenticated: {request.user.is_authenticated}")
        
        # Always allow account creation
        if view.action == 'create':
            return True
        
        # Require authentication for other actions
        if not request.user or not request.user.is_authenticated:
            return False
        
        # List view is only for superusers (view-only)
        if view.action == 'list':
            return request.user.is_superuser
        
        # Allow other actions for authenticated users
        return True

    def has_object_permission(self, request, view, obj):
        print(f"has_object_permission called - Action: {view.action}")
        print(f"Request user: {request.user}")
        print(f"Target object: {obj}")
        
        # Superusers can ONLY view accounts (read-only)
        if request.user.is_superuser:
            return view.action == 'retrieve'
        
        # Users can only access/modify their own account
        return obj == request.user
