from django.db import models


class StatutEnvoi(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    ENVOYEE = 'ENVOYEE', 'Envoyée'
    ECHEC = 'ECHEC', 'Échec'
