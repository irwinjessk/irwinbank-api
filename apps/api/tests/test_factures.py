from unittest.mock import patch

from django.core import mail

from apps.api.tests.support import ApiTestCase
from apps.audit.models import JournalAudit
from apps.facturation.models import Facture


class FacturesApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.compte = self.creer_compte(self.creer_client(self.creer_banque()))

    def deposer(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post('/api/v1/transactions/', {
                'type_transaction': 'DEPOT', 'compte': self.compte.id, 'montant': '75.00',
            }, format='json')
        return Facture.objects.get()

    def test_facture_envoyee_apres_depot(self):
        facture = self.deposer()
        self.assertEqual(facture.statut_envoi, 'ENVOYEE')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['aya@example.com'])
        self.assertIn(facture.numero_facture, mail.outbox[0].subject)

    def test_echec_envoi_marque_la_facture(self):
        with patch('apps.courrier.services.envoi.send_mail', side_effect=OSError('smtp')):
            facture = self.deposer()
        self.assertEqual(facture.statut_envoi, 'ECHEC')

    def test_renvoyer(self):
        with patch('apps.courrier.services.envoi.send_mail', side_effect=OSError('smtp')):
            facture = self.deposer()
        response = self.client.post(f'/api/v1/factures/{facture.id}/renvoyer/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['statut_envoi'], 'ENVOYEE')
        self.assertTrue(JournalAudit.objects.filter(action='facture.renvoyee').exists())

    def test_filtre_par_statut(self):
        self.deposer()
        self.assertEqual(len(self.client.get('/api/v1/factures/?statut_envoi=ECHEC').data), 0)
        self.assertEqual(len(self.client.get('/api/v1/factures/?statut_envoi=ENVOYEE').data), 1)
