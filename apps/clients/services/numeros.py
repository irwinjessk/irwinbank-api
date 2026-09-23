import secrets

from django.utils import timezone


def generer_numero(prefixe):
    mois = timezone.localtime().strftime('%Y%m')
    return f'{prefixe}-{mois}-{secrets.randbelow(1_000_000):06d}'
