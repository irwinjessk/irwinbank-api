from django.conf import settings
from django.utils import timezone

from apps.audit.services.journal import tracer
from apps.courrier.services.envoi import envoyer


def envoyer_code_activation(client, code, expire_le, acteur=None):
    corps = (
        f'Bonjour {client.prenom} {client.nom},\n\n'
        f'Votre agence {client.agence.nom} vient d’ouvrir votre espace client en ligne {client.banque.nom}.\n\n'
        f'Numéro client : {client.numero_client}\n'
        f'Code d’activation : {code}\n'
        f'Valable jusqu’au {timezone.localtime(expire_le):%d/%m/%Y à %H:%M}\n\n'
        f'Pour choisir votre mot de passe : {settings.FRONTEND_URL}/activer\n\n'
        f'Ce code est personnel et ne sert qu’une fois. Si vous n’êtes pas à l’origine de cette demande, '
        f'contactez votre agence.\n\n'
        f'ADA BANK'
    )
    statut = envoyer(client.email, f'Activez votre espace client {client.banque.nom}', corps)
    resultat = 'envoyé' if statut == 'ENVOYEE' else 'échec d’envoi'
    tracer(
        acteur=acteur,
        action='client.espace_code_envoye',
        entite='client',
        entite_id=client.id,
        resume=f'Code d’activation envoyé à {client.email} : {resultat}'[:255],
        banque=client.banque,
    )
    return statut
