from django.contrib import admin

from apps.facturation.models import Facture


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('numero_facture', 'email_destinataire', 'montant', 'statut_envoi', 'cree_le')
    list_filter = ('statut_envoi',)
