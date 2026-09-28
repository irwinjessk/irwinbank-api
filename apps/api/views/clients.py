from django.db import transaction
from django.db.models import Q
from django.utils import timezone
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
from apps.comptes.enums.compte import StatutCompte
from apps.courrier.services.bienvenue import envoyer_bienvenue_client


class ClientViewSet(PerimetreMixin, viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [IsPersonnel]
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    def get_queryset(self):
        queryset = self.restreindre(Client.objects.select_related('banque', 'agence', 'conseiller'))
        params = self.request.query_params
        banque = filtres.entier(params, 'banque')
        agence = filtres.entier(params, 'agence')
        nom = params.get('nom')
        email = params.get('email')
        numero = params.get('numero_client')
        if self.action == 'list':
            statut = params.get('statut', 'actifs')
            if statut == 'archives':
                queryset = queryset.filter(archive=True)
            elif statut != 'tous':
                queryset = queryset.filter(archive=False)
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
        acteur = self.request.user
        transaction.on_commit(lambda: envoyer_bienvenue_client(client, acteur))

    def perform_update(self, serializer):
        client = serializer.instance
        verifier_agence(self.request.user, client.agence_id)
        self.refuser_si_archive(client)
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

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def archiver(self, request, pk=None):
        client = self.get_object()
        verifier_agence(request.user, client.agence_id)
        self.refuser_si_archive(client)
        motif = (request.data.get('motif') or '').strip()
        if not motif:
            raise ValidationError({'motif': ['Indiquez le motif de l’archivage.']})
        if client.comptes.filter(statut=StatutCompte.OUVERT).exists():
            raise Conflit('Ce client a encore des comptes ouverts : clôturez-les avant d’archiver la fiche.')
        client.archive = True
        client.date_archivage = timezone.now()
        client.archive_par = request.user
        client.motif_archivage = motif[:255]
        client.save(update_fields=['archive', 'date_archivage', 'archive_par', 'motif_archivage'])
        self.tracer(client, 'client.archive', f'{client.numero_client} · archivé : {motif}')
        return Response(self.get_serializer(client).data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def restaurer(self, request, pk=None):
        client = self.get_object()
        verifier_agence(request.user, client.agence_id)
        if not client.archive:
            raise Conflit('Ce client n’est pas archivé.')
        client.archive = False
        client.date_archivage = None
        client.archive_par = None
        client.motif_archivage = ''
        client.save(update_fields=['archive', 'date_archivage', 'archive_par', 'motif_archivage'])
        self.tracer(client, 'client.restaure', f'{client.numero_client} · fiche restaurée')
        return Response(self.get_serializer(client).data)

    @action(detail=True, methods=['post'], url_path='changer-agence')
    @transaction.atomic
    def changer_agence(self, request, pk=None):
        client = self.get_object()
        verifier_agence(request.user, client.agence_id)
        self.refuser_si_archive(client)
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

    def refuser_si_archive(self, client):
        if client.archive:
            raise Conflit('Ce client est archivé : restaurez sa fiche avant toute modification.')

    def tracer(self, client, action, resume):
        tracer(
            acteur=self.request.user,
            action=action,
            entite='client',
            entite_id=client.id,
            resume=resume[:255],
            banque=client.banque,
        )
