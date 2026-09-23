from django.conf import settings
from django.db import models


class JournalAudit(models.Model):
    acteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audits',
    )
    action = models.CharField(max_length=50)
    entite = models.CharField(max_length=30)
    entite_id = models.BigIntegerField()
    banque = models.ForeignKey(
        'banques.Banque',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audits',
    )
    resume = models.CharField(max_length=255)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'journal_audit'
        ordering = ['-cree_le']

    def __str__(self):
        return f'{self.action} {self.entite}:{self.entite_id}'
