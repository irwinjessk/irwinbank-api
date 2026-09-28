from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.enums.role import Role
from apps.api import filtres
from apps.api.exceptions import Conflit
from apps.api.perimetre import PerimetreMixin
from apps.api.permissions import IsAdminOrReadOnly
from apps.api.serializers.agences import AgenceSerializer
from apps.banques.models import Agence


class AgenceViewSet(PerimetreMixin, viewsets.ModelViewSet):
    serializer_class = AgenceSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = self.restreindre(
            Agence.objects.select_related('banque').annotate(
                nombre_clients=Count('clients', distinct=True),
                nombre_agents=Count('agents', distinct=True),
            )
        )
        banque = filtres.entier(self.request.query_params, 'banque')
        if banque:
            queryset = queryset.filter(banque_id=banque)
        return queryset

    def perform_destroy(self, instance):
        if instance.est_principale:
            raise Conflit('L’agence principale ne peut pas être supprimée.')
        if instance.clients.exists() or instance.agents.exists():
            raise Conflit('Cette agence a des clients ou des agents : transférez-les ou désactivez l’agence.')
        instance.delete()

    @action(detail=True, methods=['get'])
    def agents(self, request, pk=None):
        agence = self.get_object()
        agents = agence.agents.filter(role=Role.AGENT).select_related('user').order_by('user__username')
        return Response([{'id': profil.user_id, 'username': profil.user.username} for profil in agents])
