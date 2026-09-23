from rest_framework.permissions import BasePermission

from apps.accounts.enums.role import Role


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        profil = getattr(request.user, 'profil', None)
        return bool(request.user and request.user.is_authenticated and profil and profil.role == Role.ADMIN)


class IsAgent(BasePermission):
    def has_permission(self, request, view):
        profil = getattr(request.user, 'profil', None)
        return bool(request.user and request.user.is_authenticated and profil and profil.role == Role.AGENT)
