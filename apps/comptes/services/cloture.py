from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services.journal import tracer
from apps.comptes.enums.compte import ModeRestitution, MotifCloture, StatutCompte
from apps.comptes.models import Compte
from apps.operations.enums.transaction import TypeTransaction
from apps.operations.services.enregistrer import enregistrer


@db_transaction.atomic
def cloturer(compte, *, motif, mode_restitution=None, compte_destinataire_id=None, acteur=None):
    """Restitue le solde puis clôture, en une seule transaction."""
    if motif not in MotifCloture.values:
        raise ValidationError({'motif': ['Motif de clôture invalide.']})

    compte = Compte.objects.select_for_update().select_related('client__banque').get(pk=compte.pk)
    if compte.statut == StatutCompte.CLOTURE:
        raise ValidationError('Ce compte est déjà clôturé.')

    solde = compte.solde
    restitution = ''
    if solde > 0:
        if mode_restitution not in ModeRestitution.values:
            raise ValidationError({'mode_restitution': ['Choisissez comment restituer le solde au client.']})
        if mode_restitution == ModeRestitution.VIREMENT:
            if not compte_destinataire_id:
                raise ValidationError({'compte_destinataire': ['Indiquez le compte qui reçoit le solde.']})
            enregistrer(
                type_transaction=TypeTransaction.VIREMENT,
                compte_id=compte.pk,
                compte_contrepartie_id=compte_destinataire_id,
                montant=solde,
                description='Solde de clôture',
                acteur=acteur,
            )
        else:
            enregistrer(
                type_transaction=TypeTransaction.RETRAIT,
                compte_id=compte.pk,
                montant=solde,
                description=f'Solde de clôture ({ModeRestitution(mode_restitution).label.lower()})',
                acteur=acteur,
            )
        restitution = f', {solde} restitués par {ModeRestitution(mode_restitution).label.lower()}'
        compte.refresh_from_db()

    if compte.solde != 0:
        raise ValidationError('Le solde doit être à zéro pour clôturer le compte.')

    compte.statut = StatutCompte.CLOTURE
    compte.date_cloture = timezone.now()
    compte.save(update_fields=['statut', 'date_cloture'])
    tracer(
        acteur=acteur if getattr(acteur, 'is_authenticated', False) else None,
        action='compte.cloture',
        entite='compte',
        entite_id=compte.id,
        resume=f'Clôture de {compte.numero_compte} : {MotifCloture(motif).label.lower()}{restitution}',
        banque=compte.client.banque,
    )
    return compte
