from rest_framework import permissions


class UserPermission(permissions.BasePermission):
    """Checks if user id given in a URL is the same as that of currently
    authenticated user.
    """
    message = {
        "status_code": 403,
        "detail": "You do not have permission to perform this action."
    }

    def has_permission(self, request, view):
        return request.user.id == view.kwargs.get("user_id")
