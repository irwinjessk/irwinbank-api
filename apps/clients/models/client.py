from django.conf import settings
from django.db import models

from apps.clients.services.numeros import generer_numero


class Client(models.Model):
    nom = models.CharField(max_length=80)
    prenom = models.CharField(max_length=80)
    email = models.EmailField(unique=True)
    numero_client = models.CharField(max_length=20, unique=True, blank=True)
    banque = models.ForeignKey(
        'banques.Banque',
        on_delete=models.PROTECT,
        related_name='clients',
    )
    agence = models.ForeignKey(
        'banques.Agence',
        on_delete=models.PROTECT,
        related_name='clients',
    )
    conseiller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='clients_suivis',
    )
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'client'
        ordering = ['nom', 'prenom']

    def save(self, *args, **kwargs):
        if not self.numero_client:
            self.numero_client = generer_numero('CLI')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.prenom} {self.nom}'
