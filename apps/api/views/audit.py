from rest_framework import viewsets

from apps.api import filtres
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
        date_min = filtres.jour(params, 'date_min')
        date_max = filtres.jour(params, 'date_max')
        if date_min:
            queryset = queryset.filter(cree_le__date__gte=date_min)
        if date_max:
            queryset = queryset.filter(cree_le__date__lte=date_max)
        return queryset
