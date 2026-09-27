from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.serializers.comptes import CompteSerializer
from apps.comptes.models import Compte
from apps.comptes.services.cloture import cloturer


class CompteViewSet(viewsets.ModelViewSet):
    serializer_class = CompteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Compte.objects.select_related('client', 'client__banque')
        client = self.request.query_params.get('client')
        if client:
            queryset = queryset.filter(client_id=client)
        return queryset

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        compte = cloturer(self.get_object())
        return Response(self.get_serializer(compte).data)
