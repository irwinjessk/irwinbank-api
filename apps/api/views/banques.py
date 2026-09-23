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
        return Banque.objects.annotate(nombre_clients=Count('clients'))

    @action(detail=False, methods=['get'])
    def top(self, request):
        banques = self.get_queryset().order_by('-nombre_clients', 'nom')[:15]
        return Response(self.get_serializer(banques, many=True).data)
