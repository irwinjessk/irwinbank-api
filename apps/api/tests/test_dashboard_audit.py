from apps.api.tests.support import ApiTestCase


class DashboardAuditTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.banque = self.creer_banque()
        self.autre_banque = self.creer_banque(nom='Autre')
        self.source = self.creer_compte(self.creer_client(self.banque, email='a@example.com'))
        self.cible = self.creer_compte(self.creer_client(self.banque, email='b@example.com'))
        self.externe = self.creer_compte(self.creer_client(self.autre_banque, email='c@example.com'))
        for data in (
            {'type_transaction': 'DEPOT', 'compte': self.source.id, 'montant': '100.00'},
            {'type_transaction': 'VIREMENT', 'compte': self.source.id, 'compte_contrepartie': self.cible.id, 'montant': '30.00'},
            {'type_transaction': 'DEPOT', 'compte': self.externe.id, 'montant': '500.00'},
        ):
            self.client.post('/api/v1/transactions/', data, format='json')

    def par_type(self, response):
        return {ligne['type']: ligne for ligne in response.data['transactions_par_type']}

    def test_dashboard_admin(self):
        response = self.client.get('/api/v1/dashboard/')
        self.assertEqual(response.status_code, 200)
        types = self.par_type(response)
        self.assertEqual(types['DEPOT'], {'type': 'DEPOT', 'nombre': 2, 'volume': '600.00'})
        self.assertEqual(types['VIREMENT']['nombre'], 1)
        self.assertEqual(types['VIREMENT']['volume'], '30.00')
        self.assertIn('top_banques', response.data)
        self.assertEqual(response.data['comptes_par_statut'][0], {'statut': 'OUVERT', 'nombre': 3})

    def test_dashboard_agent_limite_a_sa_banque(self):
        self.connecter_agent(self.banque)
        response = self.client.get('/api/v1/dashboard/')
        self.assertNotIn('top_banques', response.data)
        self.assertEqual(self.par_type(response)['DEPOT']['volume'], '100.00')

    def test_audit_filtre_et_perimetre(self):
        self.assertEqual(len(self.client.get('/api/v1/audit/?action=deposee').data), 2)
        self.connecter_agent(self.banque)
        lignes = self.client.get('/api/v1/audit/').data
        self.assertEqual(len(lignes), 2)
        self.assertTrue(all(ligne['banque'] == self.banque.id for ligne in lignes))
        self.assertEqual(lignes[0]['acteur_nom'], 'admin')

    def test_audit_en_lecture_seule(self):
        self.assertEqual(self.client.post('/api/v1/audit/', {}).status_code, 405)
