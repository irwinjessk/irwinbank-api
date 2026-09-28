from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.enums.role import ROLES_PERSONNEL, Role
from apps.api.perimetre import client_de, role_de


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and role_de(request.user) == Role.ADMIN)


class IsAgent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and role_de(request.user) == Role.AGENT)


class IsPersonnel(BasePermission):
    message = 'Aucun rôle ADMIN ou AGENT n’est attribué à ce compte.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and role_de(request.user) in ROLES_PERSONNEL)


class IsClient(BasePermission):
    message = 'Espace réservé aux clients dont l’accès en ligne est actif.'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        client = client_de(request.user)
        return bool(client and not client.archive)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not IsPersonnel().has_permission(request, view):
            self.message = IsPersonnel.message
            return False
        self.message = 'Action réservée à un administrateur.'
        return request.method in SAFE_METHODS or role_de(request.user) == Role.ADMIN
