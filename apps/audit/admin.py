from django.contrib import admin

from apps.audit.models import JournalAudit


@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    list_display = ('cree_le', 'action', 'entite', 'entite_id', 'acteur')
    list_filter = ('entite', 'action')
    search_fields = ('resume',)
