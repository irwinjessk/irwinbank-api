from django.utils import timezone

from apps.audit.services.formats import montant_fr
from apps.courrier.services.envoi import envoyer
from apps.facturation.enums.facture import StatutEnvoi


def envoyer_facture(facture):
    transaction = facture.transaction
    corps = (
        f'Bonjour,\n\n'
        f'Votre opération {transaction.get_type_transaction_display().lower()} '
        f'du {timezone.localtime(transaction.date_transaction):%d/%m/%Y %H:%M} '
        f'a été enregistrée.\n\n'
        f'Facture : {facture.numero_facture}\n'
        f'Compte : {transaction.compte.numero_compte}\n'
        f'Montant : {montant_fr(facture.montant)}\n\n'
        f'ADA BANK'
    )
    statut = envoyer(facture.email_destinataire, f'ADA BANK · Facture {facture.numero_facture}', corps)
    facture.statut_envoi = StatutEnvoi.ENVOYEE if statut == 'ENVOYEE' else StatutEnvoi.ECHEC
    facture.envoye_le = timezone.now() if statut == 'ENVOYEE' else None
    facture.save(update_fields=['statut_envoi', 'envoye_le'])
    return facture
