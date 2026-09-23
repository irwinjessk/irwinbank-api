from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.serializers.audit import JournalAuditSerializer
from apps.audit.models import JournalAudit


class JournalAuditViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JournalAudit.objects.all()
    serializer_class = JournalAuditSerializer
    permission_classes = [IsAuthenticated]
