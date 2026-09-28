from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.api import filtres
from apps.api.exceptions import Conflit
from apps.api.perimetre import PerimetreMixin, verifier_agence, verifier_banque
from apps.api.permissions import IsPersonnel
from apps.api.serializers.clients import ClientSerializer
from apps.audit.services.journal import tracer
from apps.banques.models import Agence
from apps.clients.models import Client


class ClientViewSet(PerimetreMixin, viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [IsPersonnel]

    def get_queryset(self):
        queryset = self.restreindre(Client.objects.select_related('banque', 'agence', 'conseiller'))
        params = self.request.query_params
        banque = filtres.entier(params, 'banque')
        agence = filtres.entier(params, 'agence')
        nom = params.get('nom')
        email = params.get('email')
        numero = params.get('numero_client')
        if banque:
            queryset = queryset.filter(banque_id=banque)
        if agence:
            queryset = queryset.filter(agence_id=agence)
        if params.get('sans_conseiller') in ('1', 'true'):
            queryset = queryset.filter(conseiller__isnull=True)
        if nom:
            queryset = queryset.filter(Q(nom__icontains=nom) | Q(prenom__icontains=nom))
        if email:
            queryset = queryset.filter(email__icontains=email)
        if numero:
            queryset = queryset.filter(numero_client__icontains=numero)
        return queryset

    def perform_create(self, serializer):
        verifier_banque(self.request.user, serializer.validated_data['banque'].id)
        verifier_agence(self.request.user, serializer.validated_data['agence'].id)
        client = serializer.save()
        self.tracer(client, 'client.cree', f'Inscription de {client.prenom} {client.nom} ({client.numero_client}) à {client.agence.nom}')

    def perform_update(self, serializer):
        client = serializer.instance
        verifier_agence(self.request.user, client.agence_id)
        champs = ('nom', 'prenom', 'email', 'conseiller')
        avant = {champ: getattr(client, champ) for champ in champs}
        client = serializer.save()
        changements = [
            f'{champ} : {avant[champ] or "aucun"} → {getattr(client, champ) or "aucun"}'
            for champ in champs
            if avant[champ] != getattr(client, champ)
        ]
        if changements:
            self.tracer(client, 'client.modifie', f'{client.numero_client} · ' + ', '.join(changements))

    def perform_destroy(self, instance):
        verifier_agence(self.request.user, instance.agence_id)
        if instance.comptes.exists():
            raise Conflit('Ce client a des comptes : ils doivent rester archivés, la fiche ne peut pas être supprimée.')
        self.tracer(instance, 'client.supprime', f'Suppression de {instance.prenom} {instance.nom} ({instance.numero_client})')
        instance.delete()

    @action(detail=True, methods=['post'], url_path='changer-agence')
    @transaction.atomic
    def changer_agence(self, request, pk=None):
        client = self.get_object()
        verifier_agence(request.user, client.agence_id)
        agence_id = filtres.entier(request.data, 'agence')
        if not agence_id:
            raise ValidationError({'agence': ['Choisissez la nouvelle agence.']})
        nouvelle = Agence.objects.filter(pk=agence_id, banque_id=client.banque_id, actif=True).first()
        if nouvelle is None:
            raise ValidationError({'agence': ['Agence introuvable dans la banque du client.']})
        if nouvelle.id == client.agence_id:
            raise ValidationError({'agence': ['Le client est déjà rattaché à cette agence.']})

        ancienne = client.agence
        client.agence = nouvelle
        conseiller_retire = client.conseiller_id and getattr(client.conseiller.profil, 'agence_id', None) != nouvelle.id
        if conseiller_retire:
            client.conseiller = None
        client.save(update_fields=['agence', 'conseiller'])
        self.tracer(
            client,
            'client.agence_changee',
            f'{client.numero_client} · {ancienne.nom} → {nouvelle.nom}' + (' (conseiller à redésigner)' if conseiller_retire else ''),
        )
        return Response(self.get_serializer(client).data)

    def tracer(self, client, action, resume):
        tracer(
            acteur=self.request.user,
            action=action,
            entite='client',
            entite_id=client.id,
            resume=resume[:255],
            banque=client.banque,
        )
