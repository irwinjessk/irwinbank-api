from rest_framework import serializers

from apps.clients.models import Client


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('id', 'nom', 'prenom', 'email', 'numero_client', 'banque', 'date_inscription')
        read_only_fields = ('numero_client', 'date_inscription')
