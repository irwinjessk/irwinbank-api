from django.db import models


class Role(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrateur'
    AGENT = 'AGENT', 'Agent de banque'
    CLIENT = 'CLIENT', 'Client (espace en ligne)'


ROLES_PERSONNEL = (Role.ADMIN, Role.AGENT)
