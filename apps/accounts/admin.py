from django.contrib import admin

from apps.accounts.models import Profil


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'banque')
    list_filter = ('role',)
