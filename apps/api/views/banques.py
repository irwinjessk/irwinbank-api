from django.db import transaction
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.api.exceptions import Conflit
from apps.api.perimetre import PerimetreMixin, banque_agent
from apps.api.permissions import IsAdminOrReadOnly
from apps.api.serializers.banques import BanqueSerializer
from apps.banques.models import Banque


class BanqueViewSet(PerimetreMixin, viewsets.ModelViewSet):
    serializer_class = BanqueSerializer
    permission_classes = [IsAdminOrReadOnly]
    champ_banque = 'id'

    def get_queryset(self):
        queryset = self.restreindre(Banque.objects.annotate(nombre_clients=Count('clients')))
        pays = self.request.query_params.get('pays')
        ville = self.request.query_params.get('ville')
        if pays:
            queryset = queryset.filter(pays__icontains=pays)
        if ville:
            queryset = queryset.filter(ville__icontains=ville)
        return queryset

    @transaction.atomic
    def perform_destroy(self, instance):
        if instance.clients.exists() or instance.agents.exists():
            raise Conflit('Cette banque a des clients ou des agents : désactivez-la plutôt que de la supprimer.')
        instance.agences.all().delete()
        instance.delete()

    @action(detail=False, methods=['get'])
    def top(self, request):
        if banque_agent(request.user) is not None:
            raise PermissionDenied('Le classement des banques est réservé à un administrateur.')
        banques = self.get_queryset().order_by('-nombre_clients', 'nom')[:15]
        return Response(self.get_serializer(banques, many=True).data)
