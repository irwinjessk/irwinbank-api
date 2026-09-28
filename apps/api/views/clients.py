from django.db.models import Q
from rest_framework import viewsets

from apps.api import filtres
from apps.api.perimetre import PerimetreMixin, verifier_banque
from apps.api.permissions import IsPersonnel
from apps.api.serializers.clients import ClientSerializer
from apps.audit.services.journal import tracer
from apps.clients.models import Client


class ClientViewSet(PerimetreMixin, viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [IsPersonnel]

    def get_queryset(self):
        queryset = self.restreindre(Client.objects.select_related('banque'))
        banque = filtres.entier(self.request.query_params, 'banque')
        nom = self.request.query_params.get('nom')
        email = self.request.query_params.get('email')
        numero = self.request.query_params.get('numero_client')
        if banque:
            queryset = queryset.filter(banque_id=banque)
        if nom:
            queryset = queryset.filter(Q(nom__icontains=nom) | Q(prenom__icontains=nom))
        if email:
            queryset = queryset.filter(email__icontains=email)
        if numero:
            queryset = queryset.filter(numero_client__icontains=numero)
        return queryset

    def perform_create(self, serializer):
        verifier_banque(self.request.user, serializer.validated_data['banque'].id)
        client = serializer.save()
        self.tracer(client, 'client.cree', f'Inscription de {client.prenom} {client.nom} ({client.numero_client})')

    def perform_update(self, serializer):
        avant = {champ: getattr(serializer.instance, champ) for champ in ('nom', 'prenom', 'email')}
        client = serializer.save()
        changements = [
            f'{champ} : {avant[champ]} → {getattr(client, champ)}'
            for champ in avant
            if avant[champ] != getattr(client, champ)
        ]
        if changements:
            self.tracer(client, 'client.modifie', f'{client.numero_client} · ' + ', '.join(changements))

    def tracer(self, client, action, resume):
        tracer(
            acteur=self.request.user,
            action=action,
            entite='client',
            entite_id=client.id,
            resume=resume[:255],
            banque=client.banque,
        )
