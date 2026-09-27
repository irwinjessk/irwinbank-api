from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.enums.role import Role
from apps.api.perimetre import role_de


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and role_de(request.user) == Role.ADMIN)


class IsAgent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and role_de(request.user) == Role.AGENT)


class IsPersonnel(BasePermission):
    message = 'Aucun rôle ADMIN ou AGENT n’est attribué à ce compte.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and role_de(request.user) is not None)


class IsAdminOrReadOnly(IsPersonnel):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.method in SAFE_METHODS or role_de(request.user) == Role.ADMIN
