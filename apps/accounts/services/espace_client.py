import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.enums.role import Role
from apps.accounts.models import ActivationEspace, Profil

ALPHABET_CODE = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
DUREE_VALIDITE_CODE = timedelta(hours=72)
TENTATIVES_MAX = 5

AUCUN = 'AUCUN'
EN_ATTENTE = 'EN_ATTENTE'
ACTIF = 'ACTIF'
DESACTIVE = 'DESACTIVE'


class ActivationRefusee(Exception):
    pass


class EspaceIndisponible(Exception):
    pass


def generer_code():
    brut = ''.join(secrets.choice(ALPHABET_CODE) for _ in range(8))
    return f'{brut[:4]}-{brut[4:]}'


def normaliser_code(code):
    brut = ''.join(caractere for caractere in (code or '').upper() if caractere.isalnum())
    return f'{brut[:4]}-{brut[4:]}'


def profil_en_ligne(client):
    try:
        return client.profil_en_ligne
    except Profil.DoesNotExist:
        return None


def etat_espace(client):
    """Statut de l'espace en ligne et, s'il y en a un, l'échéance du code en cours."""
    profil = profil_en_ligne(client)
    if profil is None:
        return {'statut': AUCUN, 'code_expire_le': None}
    user = profil.user
    activation = getattr(user, 'activation_espace', None)
    if not user.is_active:
        statut = DESACTIVE
    elif activation is not None or not user.has_usable_password():
        statut = EN_ATTENTE
    else:
        statut = ACTIF
    return {'statut': statut, 'code_expire_le': activation.expire_le if activation else None}


@transaction.atomic
def ouvrir_espace(client, acteur):
    """Crée l'accès (ou le réinitialise) et renvoie le code en clair, affiché une seule fois."""
    if client.archive:
        raise EspaceIndisponible('Ce client est archivé : restaurez sa fiche avant d’ouvrir son espace.')
    profil = profil_en_ligne(client)
    if profil is None:
        User = get_user_model()
        if User.objects.filter(username=client.numero_client).exists():
            raise EspaceIndisponible('Un utilisateur porte déjà ce numéro comme identifiant.')
        user = User.objects.create_user(username=client.numero_client, email=client.email)
        Profil.objects.create(user=user, role=Role.CLIENT, client=client)
    else:
        user = profil.user
    user.set_unusable_password()
    user.is_active = True
    user.save(update_fields=['password', 'is_active'])

    code = generer_code()
    expire_le = timezone.now() + DUREE_VALIDITE_CODE
    ActivationEspace.objects.update_or_create(
        user=user,
        defaults={'code_hash': make_password(code), 'expire_le': expire_le, 'tentatives': 0, 'cree_par': acteur},
    )
    return code, expire_le


@transaction.atomic
def desactiver_espace(client):
    profil = profil_en_ligne(client)
    if profil is None or not profil.user.is_active:
        return False
    user = profil.user
    user.is_active = False
    user.save(update_fields=['is_active'])
    ActivationEspace.objects.filter(user=user).delete()
    return True


def activer_espace(numero_client, code, mot_de_passe):
    """Valide le code remis au guichet et fixe le mot de passe. Renvoie la fiche client."""
    refus = ActivationRefusee('Numéro client ou code d’activation invalide.')
    activation = (
        ActivationEspace.objects.select_related('user__profil__client')
        .filter(user__username=(numero_client or '').strip().upper(), user__profil__role=Role.CLIENT)
        .first()
    )
    if activation is None or not activation.user.is_active:
        raise refus
    client = activation.user.profil.client
    if client.archive:
        raise refus
    if activation.expire_le < timezone.now() or activation.tentatives >= TENTATIVES_MAX:
        raise ActivationRefusee('Ce code a expiré ou a été bloqué : demandez un nouveau code à votre agence.')
    if not check_password(normaliser_code(code), activation.code_hash):
        ActivationEspace.objects.filter(pk=activation.pk).update(tentatives=F('tentatives') + 1)
        raise refus

    user = activation.user
    validate_password(mot_de_passe, user)
    with transaction.atomic():
        if not ActivationEspace.objects.filter(pk=activation.pk).delete()[0]:
            raise refus
        user.set_password(mot_de_passe)
        user.save(update_fields=['password'])
    return client
