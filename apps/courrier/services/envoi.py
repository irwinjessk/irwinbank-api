import logging

from django.core.mail import send_mail

logger = logging.getLogger(__name__)

MENTION_DEMO = (
    '\n\n--\n'
    'Message envoyé par une application de démonstration (projet IRWIN BANK). '
    'ADA BANK n’est pas un établissement bancaire réel.'
)


def envoyer(destinataire, sujet, corps):
    """Point unique d'envoi. Renvoie 'ENVOYEE' ou 'ECHEC', sans jamais lever."""
    try:
        send_mail(sujet, corps + MENTION_DEMO, None, [destinataire], fail_silently=False)
    except Exception:
        logger.exception('Échec d’envoi à %s', destinataire)
        return 'ECHEC'
    return 'ENVOYEE'
