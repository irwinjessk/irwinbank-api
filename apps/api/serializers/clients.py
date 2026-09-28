from rest_framework import serializers

from apps.clients.models import Client


class ClientSerializer(serializers.ModelSerializer):
    banque_nom = serializers.CharField(source='banque.nom', read_only=True)

    class Meta:
        model = Client
        fields = ('id', 'nom', 'prenom', 'email', 'numero_client', 'banque', 'banque_nom', 'date_inscription')
        read_only_fields = ('numero_client', 'date_inscription')

    def validate_banque(self, banque):
        if self.instance and banque != self.instance.banque:
            raise serializers.ValidationError('La banque d’un client ne peut pas être modifiée.')
        return banque
