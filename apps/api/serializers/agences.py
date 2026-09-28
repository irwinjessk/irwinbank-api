from rest_framework import serializers

from apps.banques.models import Agence


class AgenceSerializer(serializers.ModelSerializer):
    banque_nom = serializers.CharField(source='banque.nom', read_only=True)
    nombre_clients = serializers.IntegerField(read_only=True, default=0)
    nombre_agents = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Agence
        fields = (
            'id', 'nom', 'ville', 'banque', 'banque_nom', 'date_creation', 'actif',
            'nombre_clients', 'nombre_agents',
        )
        read_only_fields = ('date_creation',)

    def validate_banque(self, banque):
        if self.instance and banque != self.instance.banque:
            raise serializers.ValidationError('Une agence ne peut pas changer de banque.')
        return banque

    def validate(self, attrs):
        banque = attrs.get('banque') or self.instance.banque
        nom = attrs.get('nom') or self.instance.nom
        doublons = Agence.objects.filter(banque=banque, nom__iexact=nom)
        if self.instance:
            doublons = doublons.exclude(pk=self.instance.pk)
        if doublons.exists():
            raise serializers.ValidationError({'nom': ['Cette banque a déjà une agence portant ce nom.']})
        return attrs
