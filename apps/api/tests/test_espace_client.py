from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.utils import timezone

from apps.accounts.models import ActivationEspace
from apps.api.tests.support import ApiTestCase
from apps.audit.models import JournalAudit
from apps.operations.services.enregistrer import enregistrer

MOT_DE_PASSE = 'Horizon-Lagune-2026'


@patch('apps.api.views.clients.envoyer_code_activation')
class EspaceClientTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.banque = self.creer_banque()
        self.aya = self.creer_client(self.banque)
        self.compte = self.creer_compte(self.aya)
        autre = self.creer_client(self.banque, email='koffi@example.com', nom='Koffi')
        self.compte_autre = self.creer_compte(autre)
        enregistrer(type_transaction='DEPOT', compte_id=self.compte.id, montant='50000', acteur=self.user)
        enregistrer(type_transaction='DEPOT', compte_id=self.compte_autre.id, montant='90000', acteur=self.user)

    def ouvrir(self, client=None):
        with self.captureOnCommitCallbacks(execute=True):
            reponse = self.client.post(f'/api/v1/clients/{(client or self.aya).id}/activer-espace/')
        self.assertEqual(reponse.status_code, 200, reponse.data)
        return reponse.data['code']

    def activer(self, code, mot_de_passe=MOT_DE_PASSE, numero=None):
        return self.client.post('/api/v1/espace-client/activation/', {
            'numero_client': numero or self.aya.numero_client, 'code': code, 'mot_de_passe': mot_de_passe,
        }, format='json')

    def connecter_client(self):
        self.activer(self.ouvrir())
        self.client.force_authenticate(None)
        reponse = self.client.post('/api/v1/auth/login', {'username': self.aya.numero_client, 'password': MOT_DE_PASSE}, format='json')
        self.assertEqual(reponse.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {reponse.data["access"]}')

    def test_parcours_complet_activation_puis_connexion(self, envoi):
        self.assertEqual(self.client.get(f'/api/v1/clients/{self.aya.id}/').data['espace']['statut'], 'AUCUN')
        code = self.ouvrir()
        self.assertRegex(code, r'^[A-Z2-9]{4}-[A-Z2-9]{4}$')
        envoi.assert_called_once()
        self.assertEqual(self.client.get(f'/api/v1/clients/{self.aya.id}/').data['espace']['statut'], 'EN_ATTENTE')

        self.assertEqual(self.activer(code.lower().replace('-', '')).status_code, 200)
        self.assertEqual(self.client.get(f'/api/v1/clients/{self.aya.id}/').data['espace']['statut'], 'ACTIF')
        self.assertEqual(self.activer(code).status_code, 400)

        self.client.force_authenticate(None)
        connexion = self.client.post('/api/v1/auth/login', {'username': self.aya.numero_client, 'password': MOT_DE_PASSE}, format='json')
        self.assertEqual(connexion.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {connexion.data["access"]}')
        moi = self.client.get('/api/v1/auth/me').data
        self.assertEqual(moi['role'], 'CLIENT')
        self.assertEqual(moi['client']['numero_client'], self.aya.numero_client)
        actions = set(JournalAudit.objects.filter(entite='client', entite_id=self.aya.id).values_list('action', flat=True))
        self.assertTrue({'client.espace_code_genere', 'client.espace_active'} <= actions)

    def test_le_code_n_apparait_pas_dans_le_journal(self, envoi):
        code = self.ouvrir()
        self.assertFalse(JournalAudit.objects.filter(resume__contains=code).exists())
        self.assertNotEqual(ActivationEspace.objects.get().code_hash, code)

    def test_code_errone_bloque_apres_cinq_tentatives(self, envoi):
        code = self.ouvrir()
        for _ in range(5):
            self.assertEqual(self.activer('AAAA-AAAA').status_code, 400)
        reponse = self.activer(code)
        self.assertEqual(reponse.status_code, 400)
        self.assertIn('nouveau code', str(reponse.data))

    def test_code_expire_refuse(self, envoi):
        code = self.ouvrir()
        ActivationEspace.objects.update(expire_le=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.activer(code).status_code, 400)

    def test_mot_de_passe_trop_faible_refuse_sans_consommer_le_code(self, envoi):
        code = self.ouvrir()
        reponse = self.activer(code, mot_de_passe='1234')
        self.assertEqual(reponse.status_code, 400)
        self.assertIn('mot_de_passe', reponse.data)
        self.assertEqual(self.activer(code).status_code, 200)

    def test_numero_inconnu_meme_message(self, envoi):
        code = self.ouvrir()
        reponse = self.activer(code, numero='CLI-000000-000000')
        self.assertEqual(reponse.status_code, 400)
        self.assertIn('invalide', str(reponse.data))

    def test_client_exclu_du_back_office(self, envoi):
        self.connecter_client()
        for url in ('/api/v1/clients/', '/api/v1/comptes/', '/api/v1/transactions/', '/api/v1/factures/',
                    '/api/v1/banques/', '/api/v1/agences/', '/api/v1/audit/', '/api/v1/dashboard/'):
            self.assertEqual(self.client.get(url).status_code, 403, url)
        reponse = self.client.post('/api/v1/transactions/', {'type_transaction': 'DEPOT', 'compte': self.compte.id, 'montant': '10'}, format='json')
        self.assertEqual(reponse.status_code, 403)

    def test_personnel_exclu_de_l_espace_client(self, envoi):
        self.assertEqual(self.client.get('/api/v1/espace-client/comptes/').status_code, 403)
        self.assertEqual(self.client.get('/api/v1/espace-client/profil/').status_code, 403)

    def test_client_ne_voit_que_ses_donnees(self, envoi):
        self.connecter_client()
        comptes = self.client.get('/api/v1/espace-client/comptes/').data
        self.assertEqual([c['id'] for c in comptes], [self.compte.id])
        self.assertEqual(self.client.get(f'/api/v1/espace-client/comptes/{self.compte_autre.id}/').status_code, 404)
        operations = self.client.get('/api/v1/espace-client/transactions/').data
        self.assertEqual({o['compte'] for o in operations}, {self.compte.id})
        self.assertEqual(self.client.get(f'/api/v1/espace-client/transactions/?compte={self.compte_autre.id}').data, [])
        factures = self.client.get('/api/v1/espace-client/factures/').data
        self.assertEqual(len(factures), 1)

    def test_client_ne_peut_rien_ecrire_sur_ses_comptes(self, envoi):
        self.connecter_client()
        self.assertEqual(self.client.post('/api/v1/espace-client/comptes/', {'client': self.aya.id, 'type_compte': 'EPARGNE'}).status_code, 405)
        self.assertEqual(self.client.post(f'/api/v1/espace-client/comptes/{self.compte.id}/cloturer/').status_code, 405)
        self.assertEqual(self.client.post('/api/v1/espace-client/transactions/', {}).status_code, 405)

    def test_releve_pdf_du_client(self, envoi):
        self.connecter_client()
        reponse = self.client.get(f'/api/v1/espace-client/transactions/export/?format=pdf&compte={self.compte.id}')
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.content.startswith(b'%PDF'))
        self.assertIn('releve-', reponse['Content-Disposition'])

    def test_modifier_email_et_mot_de_passe(self, envoi):
        self.connecter_client()
        reponse = self.client.patch('/api/v1/espace-client/profil/', {'email': 'aya.new@example.com', 'nom': 'Pirate'}, format='json')
        self.assertEqual(reponse.status_code, 200)
        self.aya.refresh_from_db()
        self.assertEqual((self.aya.email, self.aya.nom), ('aya.new@example.com', 'Kouassi'))
        self.assertEqual(self.client.patch('/api/v1/espace-client/profil/', {'email': 'koffi@example.com'}, format='json').status_code, 400)

        self.assertEqual(self.client.post('/api/v1/espace-client/mot-de-passe/', {'ancien': 'faux', 'nouveau': 'Autre-Horizon-2027'}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/v1/espace-client/mot-de-passe/', {'ancien': MOT_DE_PASSE, 'nouveau': 'Autre-Horizon-2027'}, format='json').status_code, 204)
        actions = set(JournalAudit.objects.values_list('action', flat=True))
        self.assertTrue({'client.email_modifie', 'client.mot_de_passe_modifie'} <= actions)

    def test_archivage_coupe_l_acces(self, envoi):
        self.connecter_client()
        self.client.credentials()
        self.client.force_authenticate(self.user)
        self.compte.statut = 'CLOTURE'
        self.compte.save(update_fields=['statut'])
        self.assertEqual(self.client.post(f'/api/v1/clients/{self.aya.id}/archiver/', {'motif': 'Départ'}).status_code, 200)
        self.assertEqual(self.client.get(f'/api/v1/clients/{self.aya.id}/').data['espace']['statut'], 'DESACTIVE')
        self.client.force_authenticate(None)
        connexion = self.client.post('/api/v1/auth/login', {'username': self.aya.numero_client, 'password': MOT_DE_PASSE}, format='json')
        self.assertEqual(connexion.status_code, 401)

    def test_desactivation_puis_nouveau_code(self, envoi):
        self.activer(self.ouvrir())
        self.assertEqual(self.client.post(f'/api/v1/clients/{self.aya.id}/desactiver-espace/').data['espace']['statut'], 'DESACTIVE')
        self.assertEqual(self.client.post(f'/api/v1/clients/{self.aya.id}/desactiver-espace/').status_code, 409)
        code = self.ouvrir()
        self.assertEqual(self.activer(code, mot_de_passe='Nouveau-Depart-2026').status_code, 200)

    def test_agent_d_une_autre_agence_ne_peut_pas_ouvrir_l_espace(self, envoi):
        self.connecter_agent(self.banque, self.creer_agence(self.banque))
        self.assertEqual(self.client.post(f'/api/v1/clients/{self.aya.id}/activer-espace/').status_code, 403)
