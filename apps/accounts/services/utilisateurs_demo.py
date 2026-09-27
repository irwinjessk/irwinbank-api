from django.contrib.auth import get_user_model
from django.db import transaction

from apps.accounts.enums.role import Role
from apps.accounts.models import Profil
from apps.banques.models import Banque

BANQUES_DEMO = (
    {'nom': 'ADA Abidjan', 'pays': "Côte d'Ivoire", 'ville': 'Abidjan'},
    {'nom': 'ADA Dakar', 'pays': 'Sénégal', 'ville': 'Dakar'},
)

UTILISATEURS_DEMO = (
    {'username': 'admin_demo', 'role': Role.ADMIN, 'banque': None, 'staff': True},
    {'username': 'agent_abidjan', 'role': Role.AGENT, 'banque': 'ADA Abidjan', 'staff': False},
    {'username': 'agent_dakar', 'role': Role.AGENT, 'banque': 'ADA Dakar', 'staff': False},
)


@transaction.atomic
def creer_utilisateurs_demo(mot_de_passe):
    """Crée ou remet à jour les comptes de démonstration. Idempotent."""
    banques = {}
    for donnees in BANQUES_DEMO:
        banque, _ = Banque.objects.get_or_create(nom=donnees['nom'], defaults=donnees)
        banques[banque.nom] = banque

    User = get_user_model()
    for donnees in UTILISATEURS_DEMO:
        user, _ = User.objects.get_or_create(username=donnees['username'])
        user.is_staff = donnees['staff']
        user.is_superuser = donnees['staff']
        user.is_active = True
        user.set_password(mot_de_passe)
        user.save()
        Profil.objects.update_or_create(
            user=user,
            defaults={
                'role': donnees['role'],
                'banque': banques.get(donnees['banque']),
            },
        )
    return [donnees['username'] for donnees in UTILISATEURS_DEMO]
