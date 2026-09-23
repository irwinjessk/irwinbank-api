from django.db import models


class Role(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrateur'
    AGENT = 'AGENT', 'Agent de banque'
