from django.contrib import admin

from apps.comptes.models import Compte


@admin.register(Compte)
class CompteAdmin(admin.ModelAdmin):
    list_display = ('numero_compte', 'client', 'type_compte', 'solde', 'statut')
    list_filter = ('type_compte', 'statut')
    search_fields = ('numero_compte',)
