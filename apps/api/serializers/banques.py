from rest_framework import serializers

from apps.banques.models import Banque


class BanqueSerializer(serializers.ModelSerializer):
    nombre_clients = serializers.IntegerField(read_only=True, default=0)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = Banque
        fields = ('id', 'nom', 'pays', 'ville', 'email', 'date_creation', 'actif', 'nombre_clients')
        read_only_fields = ('date_creation',)

    def validate(self, attrs):
        if not self.instance and not attrs.get('email'):
            raise serializers.ValidationError({'email': ['L’e-mail de la banque est obligatoire pour lui envoyer son message de bienvenue.']})
        return attrs
