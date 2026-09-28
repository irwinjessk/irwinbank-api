from rest_framework import serializers

from apps.accounts.enums.role import Role
from apps.accounts.services.espace_client import etat_espace
from apps.api.perimetre import agence_agent, role_de, verifier_banque
from apps.banques.models.agence import AGENCE_PRINCIPALE, Agence
from apps.clients.models import Client


class ClientSerializer(serializers.ModelSerializer):
    banque_nom = serializers.CharField(source='banque.nom', read_only=True)
    agence = serializers.PrimaryKeyRelatedField(queryset=Agence.objects.all(), required=False)
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    conseiller_nom = serializers.CharField(source='conseiller.username', read_only=True, default=None)
    archive_par_nom = serializers.CharField(source='archive_par.username', read_only=True, default=None)
    espace = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = (
            'id', 'nom', 'prenom', 'email', 'numero_client', 'banque', 'banque_nom',
            'agence', 'agence_nom', 'conseiller', 'conseiller_nom', 'date_inscription',
            'archive', 'date_archivage', 'archive_par_nom', 'motif_archivage', 'espace',
        )
        read_only_fields = ('numero_client', 'date_inscription', 'archive', 'date_archivage', 'motif_archivage')

    def get_espace(self, client):
        return etat_espace(client)

    def validate_banque(self, banque):
        if self.instance and banque != self.instance.banque:
            raise serializers.ValidationError('La banque d’un client ne peut pas être modifiée.')
        return banque

    def validate_agence(self, agence):
        if self.instance and agence != self.instance.agence:
            raise serializers.ValidationError('Utilisez « Changer d’agence » pour déplacer un client.')
        return agence

    def validate(self, attrs):
        user = self.context['request'].user
        banque = attrs.get('banque') or getattr(self.instance, 'banque', None)
        verifier_banque(user, banque.id)

        if not self.instance and 'agence' not in attrs:
            agence_id = agence_agent(user)
            if agence_id:
                attrs['agence'] = Agence.objects.get(pk=agence_id)
            else:
                attrs['agence'] = Agence.objects.filter(banque=banque, nom=AGENCE_PRINCIPALE).first()
                if attrs['agence'] is None:
                    raise serializers.ValidationError({'agence': ['Cette banque n’a aucune agence.']})
        agence = attrs.get('agence') or self.instance.agence
        if not self.instance and not banque.actif:
            raise serializers.ValidationError({'banque': ['Cette banque est désactivée.']})
        if not self.instance and not agence.actif:
            raise serializers.ValidationError({'agence': ['Cette agence est désactivée.']})
        if agence.banque_id != banque.id:
            raise serializers.ValidationError({'agence': ['Cette agence n’appartient pas à la banque du client.']})

        if not self.instance and 'conseiller' not in attrs and role_de(user) == Role.AGENT:
            attrs['conseiller'] = user
        conseiller = attrs.get('conseiller')
        if conseiller is not None:
            profil = getattr(conseiller, 'profil', None)
            if not profil or profil.role != Role.AGENT or profil.agence_id != agence.id:
                raise serializers.ValidationError({'conseiller': ['Le conseiller doit être un agent de l’agence du client.']})
        return attrs
