from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.comptes.enums.compte import StatutCompte


def cloturer(compte):
    if compte.statut == StatutCompte.CLOTURE:
        raise ValidationError('Ce compte est déjà clôturé.')
    if compte.solde != 0:
        raise ValidationError('Le solde doit être à zéro pour clôturer le compte.')
    compte.statut = StatutCompte.CLOTURE
    compte.date_cloture = timezone.now()
    compte.save(update_fields=['statut', 'date_cloture'])
    return compte
