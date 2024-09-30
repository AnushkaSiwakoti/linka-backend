from rest_framework import permissions

class IsCloudType(permissions.BasePermission):
    def has_permission(self, request, view):
        return True  # Allow all requests for now since tokens are not needed
