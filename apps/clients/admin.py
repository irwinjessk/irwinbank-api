from django.contrib import admin

from apps.clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('numero_client', 'nom', 'prenom', 'email', 'banque')
    search_fields = ('nom', 'prenom', 'email', 'numero_client')
    list_filter = ('banque',)
