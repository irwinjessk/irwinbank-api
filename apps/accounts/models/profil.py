from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.enums.role import Role


class Profil(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profil',
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    banque = models.ForeignKey(
        'banques.Banque',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='agents',
    )

    class Meta:
        db_table = 'profil'

    def clean(self):
        if self.role == Role.AGENT and self.banque_id is None:
            raise ValidationError('Un agent doit être rattaché à une banque.')
        if self.role == Role.ADMIN and self.banque_id is not None:
            raise ValidationError('Un administrateur n’est rattaché à aucune banque.')

    def __str__(self):
        return f'{self.user} ({self.role})'
