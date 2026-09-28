from rest_framework.exceptions import PermissionDenied

from apps.accounts.enums.role import Role


def role_de(user):
    profil = getattr(user, 'profil', None)
    if profil:
        return profil.role
    if user.is_superuser:
        return Role.ADMIN
    return None


def client_de(user):
    """Fiche client liée à un compte de l'espace en ligne, sinon None."""
    if role_de(user) == Role.CLIENT:
        return user.profil.client
    return None


def banque_agent(user):
    """Banque imposée à l'utilisateur, ou None pour un administrateur."""
    if role_de(user) == Role.AGENT:
        return user.profil.banque_id
    return None


def agence_agent(user):
    """Agence de l'agent, ou None pour un administrateur."""
    if role_de(user) == Role.AGENT:
        return user.profil.agence_id
    return None


def verifier_agence(user, agence_id):
    """Gestion (fiche, comptes, virements) réservée à l'agence du client."""
    agent_agence = agence_agent(user)
    if role_de(user) == Role.AGENT and agent_agence != agence_id:
        raise PermissionDenied('Ce client est rattaché à une autre agence : seules les opérations de guichet sont possibles.')


def verifier_banque(user, banque_id):
    agent_banque = banque_agent(user)
    if agent_banque is not None and int(banque_id) != agent_banque:
        raise PermissionDenied('Cette ressource est hors de votre banque.')


class PerimetreMixin:
    """Restreint le queryset à la banque de l'agent via `champ_banque`."""

    champ_banque = 'banque_id'

    def restreindre(self, queryset):
        agent_banque = banque_agent(self.request.user)
        if agent_banque is None:
            return queryset
        return queryset.filter(**{self.champ_banque: agent_banque})
