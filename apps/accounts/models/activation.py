from django.conf import settings
from django.db import models


class ActivationEspace(models.Model):
    """Code à usage unique remis au guichet pour activer (ou réinitialiser) l'espace client."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activation_espace',
    )
    code_hash = models.CharField(max_length=128)
    expire_le = models.DateTimeField()
    tentatives = models.PositiveSmallIntegerField(default=0)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activation_espace'

    def __str__(self):
        return f'Activation de {self.user} (expire le {self.expire_le:%d/%m/%Y %H:%M})'
