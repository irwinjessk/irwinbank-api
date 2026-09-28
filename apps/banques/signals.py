from apps.banques.models.agence import AGENCE_PRINCIPALE, Agence


def creer_agence_principale(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        Agence.objects.get_or_create(banque=instance, nom=AGENCE_PRINCIPALE, defaults={'ville': instance.ville})
