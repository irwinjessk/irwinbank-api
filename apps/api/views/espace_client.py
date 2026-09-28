from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.validators import UniqueValidator
from rest_framework.views import APIView

from apps.accounts.services.espace_client import ActivationRefusee, activer_espace
from apps.api.perimetre import client_de
from apps.api.permissions import IsClient
from apps.api.serializers.clients import EMAIL_DEJA_UTILISE
from apps.api.views.comptes import CompteViewSet
from apps.api.views.factures import FactureViewSet
from apps.api.views.operations import TransactionViewSet
from apps.audit.services.journal import tracer
from apps.clients.models import Client

LECTURE_SEULE = ['get', 'head', 'options']


def _tracer_client(acteur, client, action, resume):
    tracer(acteur=acteur, action=action, entite='client', entite_id=client.id, resume=resume[:255], banque=client.banque)


def _erreurs_mot_de_passe(champ, erreur):
    return ValidationError({champ: list(erreur.messages)})


class ActivationEspaceView(APIView):
    """Premier accès : numéro client + code remis au guichet + mot de passe choisi."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'activation_espace'

    def post(self, request):
        mot_de_passe = request.data.get('mot_de_passe') or ''
        if not mot_de_passe:
            raise ValidationError({'mot_de_passe': ['Choisissez un mot de passe.']})
        try:
            client = activer_espace(request.data.get('numero_client'), request.data.get('code'), mot_de_passe)
        except ActivationRefusee as erreur:
            raise ValidationError({'code': [str(erreur)]})
        except DjangoValidationError as erreur:
            raise _erreurs_mot_de_passe('mot_de_passe', erreur)
        _tracer_client(client.profil_en_ligne.user, client, 'client.espace_active', f'{client.numero_client} · espace en ligne activé par le client')
        return Response({'numero_client': client.numero_client, 'detail': 'Espace activé : vous pouvez vous connecter.'})


class EspaceProfilSerializer(serializers.ModelSerializer):
    banque_nom = serializers.CharField(source='banque.nom', read_only=True)
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    agence_ville = serializers.CharField(source='agence.ville', read_only=True)
    conseiller_nom = serializers.CharField(source='conseiller.username', read_only=True, default=None)

    class Meta:
        model = Client
        fields = (
            'nom', 'prenom', 'email', 'numero_client', 'banque_nom',
            'agence_nom', 'agence_ville', 'conseiller_nom', 'date_inscription',
        )
        read_only_fields = ('nom', 'prenom', 'numero_client', 'date_inscription')
        extra_kwargs = {'email': {'validators': [UniqueValidator(Client.objects.all(), message=EMAIL_DEJA_UTILISE)]}}
        extra_kwargs = {'email': {'validators': [UniqueValidator(Client.objects.all(), message=EMAIL_DEJA_UTILISE)]}}


class EspaceProfilView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        return Response(EspaceProfilSerializer(client_de(request.user)).data)

    def patch(self, request):
        client = client_de(request.user)
        ancien = client.email
        serializer = EspaceProfilSerializer(client, data={'email': request.data.get('email')}, partial=True)
        serializer.is_valid(raise_exception=True)
        client = serializer.save()
        if client.email != ancien:
            request.user.email = client.email
            request.user.save(update_fields=['email'])
            _tracer_client(request.user, client, 'client.email_modifie', f'{client.numero_client} · e-mail modifié par le client : {ancien} → {client.email}')
        return Response(EspaceProfilSerializer(client).data)


class EspaceMotDePasseView(APIView):
    permission_classes = [IsClient]

    def post(self, request):
        user = request.user
        if not user.check_password(request.data.get('ancien') or ''):
            raise ValidationError({'ancien': ['Mot de passe actuel incorrect.']})
        nouveau = request.data.get('nouveau') or ''
        try:
            validate_password(nouveau, user)
        except DjangoValidationError as erreur:
            raise _erreurs_mot_de_passe('nouveau', erreur)
        user.set_password(nouveau)
        user.save(update_fields=['password'])
        client = client_de(user)
        _tracer_client(user, client, 'client.mot_de_passe_modifie', f'{client.numero_client} · mot de passe modifié par le client')
        return Response(status=204)


class EspaceMixin:
    """Réutilise une vue du back-office en la limitant, en lecture, aux données du client connecté."""

    permission_classes = [IsClient]
    http_method_names = LECTURE_SEULE
    champ_client = 'client_id'

    def restreindre(self, queryset):
        return queryset.filter(**{self.champ_client: client_de(self.request.user).id})

    def _meta(self, request, maintenant, nombre, tronque):
        lignes = super()._meta(request, maintenant, nombre, tronque)
        client = client_de(request.user)
        lignes.insert(1, f'Titulaire : {client.prenom} {client.nom} · {client.numero_client} · {client.banque.nom}')
        return lignes


class EspaceCompteViewSet(EspaceMixin, CompteViewSet):
    export_nom = 'mes-comptes'
    export_titre = 'Mes comptes'


class EspaceTransactionViewSet(EspaceMixin, TransactionViewSet):
    champ_client = 'compte__client_id'
    export_nom = 'releve'
    export_titre = 'Relevé de compte'


class EspaceFactureViewSet(EspaceMixin, FactureViewSet):
    champ_client = 'transaction__compte__client_id'
    export_nom = 'mes-factures'
    export_titre = 'Mes factures'
