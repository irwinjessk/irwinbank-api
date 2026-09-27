from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.serializers.operations import TransactionSerializer
from apps.operations.models import Transaction
from apps.operations.services.enregistrer import enregistrer


class TransactionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.select_related('compte', 'compte_contrepartie')
        params = self.request.query_params
        if params.get('compte'):
            queryset = queryset.filter(compte_id=params['compte'])
        if params.get('type'):
            queryset = queryset.filter(type_transaction=params['type'])
        if params.get('date_min'):
            queryset = queryset.filter(date_transaction__date__gte=params['date_min'])
        if params.get('date_max'):
            queryset = queryset.filter(date_transaction__date__lte=params['date_max'])
        if params.get('montant_min'):
            queryset = queryset.filter(montant__gte=params['montant_min'])
        if params.get('montant_max'):
            queryset = queryset.filter(montant__lte=params['montant_max'])
        return queryset

    def create(self, request):
        mouvements = enregistrer(
            type_transaction=request.data.get('type_transaction'),
            compte_id=request.data.get('compte'),
            montant=request.data.get('montant'),
            description=request.data.get('description', ''),
            compte_contrepartie_id=request.data.get('compte_contrepartie'),
            acteur=request.user,
        )
        return Response(self.get_serializer(mouvements, many=True).data, status=status.HTTP_201_CREATED)
