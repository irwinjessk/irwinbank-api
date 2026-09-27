import logging

from django.conf import settings

from apps.accounts.services.utilisateurs_demo import creer_utilisateurs_demo

logger = logging.getLogger(__name__)


def utilisateurs_demo_apres_migration(sender, **kwargs):
    if not settings.DEMO_USERS:
        return
    if not settings.DEMO_PASSWORD:
        logger.warning('DEMO_USERS actif mais DEMO_PASSWORD vide : aucun compte de démonstration créé.')
        return
    comptes = creer_utilisateurs_demo(settings.DEMO_PASSWORD)
    print(f"Comptes de démonstration prêts : {', '.join(comptes)}")
