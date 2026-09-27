from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    label = 'accounts'

    def ready(self):
        from apps.accounts.signals import utilisateurs_demo_apres_migration

        post_migrate.connect(
            utilisateurs_demo_apres_migration,
            sender=self,
            dispatch_uid='accounts.utilisateurs_demo',
        )
