from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.serializers.banques import BanqueSerializer
from apps.banques.models import Banque


class BanqueViewSet(viewsets.ModelViewSet):
    serializer_class = BanqueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Banque.objects.annotate(nombre_clients=Count('clients'))
        pays = self.request.query_params.get('pays')
        ville = self.request.query_params.get('ville')
        if pays:
            queryset = queryset.filter(pays__icontains=pays)
        if ville:
            queryset = queryset.filter(ville__icontains=ville)
        return queryset

    @action(detail=False, methods=['get'])
    def top(self, request):
        banques = self.get_queryset().order_by('-nombre_clients', 'nom')[:15]
        return Response(self.get_serializer(banques, many=True).data)
