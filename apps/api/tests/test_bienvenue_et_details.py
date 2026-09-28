from unittest import mock

from django.core import mail

from apps.api.tests.support import ApiTestCase
from apps.audit.models import JournalAudit
from apps.comptes.services.cloture import cloturer


class BienvenueTests(ApiTestCase):
    def test_email_de_bienvenue_a_la_banque(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                '/api/v1/banques/',
                {'nom': 'ADA Lomé', 'pays': 'Togo', 'ville': 'Lomé', 'email': 'contact@ada.tg'},
                format='json',
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['contact@ada.tg'])
        self.assertIn('ADA Lomé', mail.outbox[0].subject)
        self.assertTrue(JournalAudit.objects.filter(action='banque.bienvenue', entite_id=response.data['id']).exists())

    def test_email_obligatoire_pour_une_nouvelle_banque(self):
        response = self.client.post('/api/v1/banques/', {'nom': 'X', 'pays': 'CI', 'ville': 'A'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_email_de_bienvenue_au_client_avec_son_numero(self):
        banque = self.creer_banque()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                '/api/v1/clients/',
                {'nom': 'Koné', 'prenom': 'Awa', 'email': 'awa@example.com', 'banque': banque.id},
                format='json',
            )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['awa@example.com'])
        self.assertIn(response.data['numero_client'], mail.outbox[0].body)
        self.assertIn('Agence principale', mail.outbox[0].body)

    def test_echec_d_envoi_n_annule_pas_l_inscription(self):
        banque = self.creer_banque()
        with mock.patch('apps.courrier.services.envoi.send_mail', side_effect=OSError('smtp')):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    '/api/v1/clients/',
                    {'nom': 'Koné', 'prenom': 'Awa', 'email': 'awa@example.com', 'banque': banque.id},
                    format='json',
                )
        self.assertEqual(response.status_code, 201)
        ligne = JournalAudit.objects.get(action='client.bienvenue', entite_id=response.data['id'])
        self.assertIn('échec', ligne.resume)


class DetailCompteTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.banque = self.creer_banque()
        self.client_banque = self.creer_client(self.banque)

    def test_detail_d_un_compte(self):
        compte = self.creer_compte(self.client_banque)
        response = self.client.get(f'/api/v1/comptes/{compte.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['client_nom'], 'Aya Kouassi')
        self.assertEqual(response.data['client_numero'], self.client_banque.numero_client)
        self.assertEqual((response.data['banque_nom'], response.data['agence_nom']), ('ADA BANK', 'Agence principale'))

    def test_motif_de_cloture_conserve(self):
        compte = self.creer_compte(self.client_banque)
        cloturer(compte, motif='DECISION_BANQUE')
        response = self.client.get(f'/api/v1/comptes/{compte.id}/')
        self.assertEqual((response.data['statut'], response.data['motif_cloture']), ('CLOTURE', 'DECISION_BANQUE'))
        self.assertTrue(response.data['motif_cloture_libelle'])

    def test_comptes_par_client_et_factures_par_compte(self):
        compte = self.creer_compte(self.client_banque)
        autre = self.creer_compte(self.creer_client(self.banque, email='b@example.com'))
        self.client.post('/api/v1/transactions/', {'type_transaction': 'DEPOT', 'compte': compte.id, 'montant': '10.00'}, format='json')
        self.client.post('/api/v1/transactions/', {'type_transaction': 'DEPOT', 'compte': autre.id, 'montant': '20.00'}, format='json')
        comptes = self.client.get(f'/api/v1/comptes/?client={self.client_banque.id}')
        self.assertEqual([c['id'] for c in comptes.data], [compte.id])
        factures = self.client.get(f'/api/v1/factures/?compte={compte.id}')
        self.assertEqual([f['montant'] for f in factures.data], ['10.00'])
