from rest_framework import serializers

from apps.audit.models import JournalAudit


class JournalAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalAudit
        fields = ('id', 'acteur', 'action', 'entite', 'entite_id', 'banque', 'resume', 'cree_le')
