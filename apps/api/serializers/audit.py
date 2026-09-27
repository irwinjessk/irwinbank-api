from rest_framework import serializers

from apps.audit.models import JournalAudit


class JournalAuditSerializer(serializers.ModelSerializer):
    acteur_nom = serializers.CharField(source='acteur.username', read_only=True, default=None)

    class Meta:
        model = JournalAudit
        fields = ('id', 'acteur', 'acteur_nom', 'action', 'entite', 'entite_id', 'banque', 'resume', 'cree_le')
