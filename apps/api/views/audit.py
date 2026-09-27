from rest_framework import viewsets

from apps.api.perimetre import PerimetreMixin
from apps.api.permissions import IsPersonnel
from apps.api.serializers.audit import JournalAuditSerializer
from apps.audit.models import JournalAudit


class JournalAuditViewSet(PerimetreMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = JournalAuditSerializer
    permission_classes = [IsPersonnel]

    def get_queryset(self):
        queryset = self.restreindre(JournalAudit.objects.select_related('acteur'))
        params = self.request.query_params
        if params.get('entite'):
            queryset = queryset.filter(entite=params['entite'])
        if params.get('action'):
            queryset = queryset.filter(action__icontains=params['action'])
        if params.get('date_min'):
            queryset = queryset.filter(cree_le__date__gte=params['date_min'])
        if params.get('date_max'):
            queryset = queryset.filter(cree_le__date__lte=params['date_max'])
        return queryset
