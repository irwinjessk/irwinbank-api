from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import Profil
from apps.accounts.signals import utilisateurs_demo_apres_migration
from apps.banques.models import Banque


class UtilisateursDemoTests(TestCase):
    @override_settings(DEMO_USERS=True, DEMO_PASSWORD='DemoPass!2026')
    def test_signal_cree_les_comptes_une_seule_fois(self):
        utilisateurs_demo_apres_migration(sender=None)
        utilisateurs_demo_apres_migration(sender=None)
        self.assertEqual(
            get_user_model().objects.filter(username__in=['admin_demo', 'agent_abidjan', 'agent_cocody', 'agent_dakar']).count(), 4
        )
        self.assertEqual(Banque.objects.filter(nom__startswith='ADA ').count(), 2)
        agent = Profil.objects.get(user__username='agent_abidjan')
        self.assertEqual((agent.role, agent.banque.nom, agent.agence.nom), ('AGENT', 'ADA Abidjan', 'Agence principale'))
        cocody = Profil.objects.get(user__username='agent_cocody')
        self.assertEqual((cocody.banque.nom, cocody.agence.nom), ('ADA Abidjan', 'Cocody'))
        self.assertTrue(get_user_model().objects.get(username='admin_demo').is_superuser)

    @override_settings(DEMO_USERS=True, DEMO_PASSWORD='DemoPass!2026')
    def test_connexion_avec_un_compte_demo(self):
        utilisateurs_demo_apres_migration(sender=None)
        response = APIClient().post('/api/v1/auth/login', {'username': 'agent_dakar', 'password': 'DemoPass!2026'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    @override_settings(DEMO_USERS=True, DEMO_PASSWORD='')
    def test_rien_sans_mot_de_passe(self):
        utilisateurs_demo_apres_migration(sender=None)
        self.assertFalse(get_user_model().objects.filter(username='admin_demo').exists())

    @override_settings(DEMO_USERS=False, DEMO_PASSWORD='DemoPass!2026')
    def test_desactive_par_defaut(self):
        utilisateurs_demo_apres_migration(sender=None)
        self.assertFalse(get_user_model().objects.filter(username='admin_demo').exists())
