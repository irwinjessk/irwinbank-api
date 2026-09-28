from django.contrib import admin

from apps.banques.models import Agence, Banque


@admin.register(Banque)
class BanqueAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pays', 'ville', 'actif', 'date_creation')
    list_filter = ('pays', 'actif')
    search_fields = ('nom', 'ville')


@admin.register(Agence)
class AgenceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'banque', 'ville', 'actif')
    list_filter = ('banque', 'actif')
    search_fields = ('nom', 'ville')
