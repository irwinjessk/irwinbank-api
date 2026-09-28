from django.apps import AppConfig
from django.db.models.signals import post_save


class BanquesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.banques'
    label = 'banques'

    def ready(self):
        from apps.banques.models import Banque
        from apps.banques.signals import creer_agence_principale

        post_save.connect(creer_agence_principale, sender=Banque, dispatch_uid='banques.agence_principale')
