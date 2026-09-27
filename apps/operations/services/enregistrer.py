from decimal import Decimal, InvalidOperation
from uuid import uuid4

from django.db import transaction as db_transaction
from rest_framework.exceptions import ValidationError

from apps.audit.services.journal import tracer
from apps.comptes.enums.compte import StatutCompte
from apps.comptes.models import Compte
from apps.facturation.models import Facture
from apps.facturation.services.envoi_facture import envoyer_facture
from apps.operations.enums.transaction import Sens, TypeTransaction
from apps.operations.models import Transaction


def _montant(valeur):
    try:
        montant = Decimal(str(valeur))
    except (InvalidOperation, TypeError):
        raise ValidationError('Montant invalide.')
    if montant <= 0:
        raise ValidationError('Le montant doit être strictement positif.')
    return montant.quantize(Decimal('0.01'))


def _verrouiller(compte_id):
    try:
        compte = Compte.objects.select_for_update().select_related('client', 'client__banque').get(pk=compte_id)
    except Compte.DoesNotExist:
        raise ValidationError('Compte introuvable.')
    if compte.statut != StatutCompte.OUVERT:
        raise ValidationError('Le compte est clôturé.')
    return compte


def _facture(mouvement, compte):
    facture = Facture.objects.create(
        transaction=mouvement,
        email_destinataire=compte.client.email,
        montant=mouvement.montant,
    )
    db_transaction.on_commit(lambda: envoyer_facture(facture))
    return facture


def _tracer(acteur, action, mouvement, resume):
    tracer(
        acteur=acteur if getattr(acteur, 'is_authenticated', False) else None,
        action=action,
        entite='transaction',
        entite_id=mouvement.id,
        resume=resume,
        banque=mouvement.compte.client.banque,
    )


@db_transaction.atomic
def enregistrer(*, type_transaction, compte_id, montant, description='', compte_contrepartie_id=None, acteur=None):
    montant = _montant(montant)
    description = (description or '')[:255]

    if type_transaction == TypeTransaction.DEPOT:
        compte = _verrouiller(compte_id)
        mouvement = Transaction.objects.create(
            montant=montant,
            type_transaction=TypeTransaction.DEPOT,
            sens=Sens.CREDIT,
            compte=compte,
            description=description,
        )
        compte.solde += montant
        compte.save(update_fields=['solde'])
        _facture(mouvement, compte)
        _tracer(acteur, 'transaction.deposee', mouvement, f'Dépôt de {montant} sur {compte.numero_compte}')
        return [mouvement]

    if type_transaction == TypeTransaction.RETRAIT:
        compte = _verrouiller(compte_id)
        if compte.solde < montant:
            raise ValidationError('Solde insuffisant.')
        mouvement = Transaction.objects.create(
            montant=montant,
            type_transaction=TypeTransaction.RETRAIT,
            sens=Sens.DEBIT,
            compte=compte,
            description=description,
        )
        compte.solde -= montant
        compte.save(update_fields=['solde'])
        _facture(mouvement, compte)
        _tracer(acteur, 'transaction.retiree', mouvement, f'Retrait de {montant} sur {compte.numero_compte}')
        return [mouvement]

    if type_transaction != TypeTransaction.VIREMENT:
        raise ValidationError('Type de transaction inconnu.')
    if not compte_contrepartie_id:
        raise ValidationError('Le virement demande un compte destinataire.')
    if int(compte_id) == int(compte_contrepartie_id):
        raise ValidationError('Le compte source et le compte destinataire doivent être différents.')

    premier, second = sorted((int(compte_id), int(compte_contrepartie_id)))
    verrouilles = {
        compte.pk: compte
        for compte in Compte.objects.select_for_update().select_related('client', 'client__banque').filter(pk__in=(premier, second))
    }
    if len(verrouilles) != 2:
        raise ValidationError('Compte introuvable.')
    source = verrouilles[int(compte_id)]
    destinataire = verrouilles[int(compte_contrepartie_id)]
    for compte in (source, destinataire):
        if compte.statut != StatutCompte.OUVERT:
            raise ValidationError('Le compte est clôturé.')
    if source.solde < montant:
        raise ValidationError('Solde insuffisant.')

    reference = uuid4()
    debit = Transaction.objects.create(
        montant=montant,
        type_transaction=TypeTransaction.VIREMENT,
        sens=Sens.DEBIT,
        compte=source,
        compte_contrepartie=destinataire,
        reference_virement=reference,
        description=description,
    )
    credit = Transaction.objects.create(
        montant=montant,
        type_transaction=TypeTransaction.VIREMENT,
        sens=Sens.CREDIT,
        compte=destinataire,
        compte_contrepartie=source,
        reference_virement=reference,
        description=description,
    )
    source.solde -= montant
    destinataire.solde += montant
    source.save(update_fields=['solde'])
    destinataire.save(update_fields=['solde'])
    _facture(debit, source)
    _tracer(acteur, 'transaction.viree', debit, f'Virement de {montant} vers {destinataire.numero_compte}')
    return [debit, credit]
