from djoser.permissions import CurrentUserOrAdminOrReadOnly
from rest_framework import permissions


class CustomCurrentUserOrAdminOrReadOnly(CurrentUserOrAdminOrReadOnly):
    def has_permission(self, request, view):
        if request.path == '/api/users/me/':
            return request.user.is_authenticated
        return (request.method in permissions.SAFE_METHODS
                or super().has_permission(request, view))


class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    message = 'Изменение контента других авторов запрещено!'

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
