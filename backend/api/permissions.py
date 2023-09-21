from rest_framework import permissions


class AuthorOrAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view) -> bool:
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj) -> bool:
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_authenticated
            and (request.user == obj.author or request.user.is_staff)
        )
