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
        if 'nom' in attrs:
            attrs['nom'] = attrs['nom'].strip()
            doublons = Banque.objects.filter(nom__iexact=attrs['nom'])
            if self.instance:
                doublons = doublons.exclude(pk=self.instance.pk)
            if doublons.exists():
                raise serializers.ValidationError({'nom': ['Une banque porte déjà ce nom.']})
        return attrs
