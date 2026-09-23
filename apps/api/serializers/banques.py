from rest_framework import serializers

from apps.banques.models import Banque


class BanqueSerializer(serializers.ModelSerializer):
    nombre_clients = serializers.IntegerField(read_only=True)

    class Meta:
        model = Banque
        fields = ('id', 'nom', 'pays', 'ville', 'date_creation', 'actif', 'nombre_clients')
        read_only_fields = ('date_creation',)
