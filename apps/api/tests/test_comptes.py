from decimal import Decimal

from apps.api.tests.support import ApiTestCase
from apps.audit.models import JournalAudit
from apps.facturation.models import Facture
from apps.operations.models import Transaction


class ComptesApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.titulaire = self.creer_client(self.creer_banque())

    def test_ouverture_compte(self):
        response = self.client.post('/api/v1/comptes/', {'client': self.titulaire.id, 'type_compte': 'EPARGNE'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['statut'], 'OUVERT')
        self.assertEqual(response.data['solde'], '0.00')
        self.assertFalse(Transaction.objects.exists())
        self.assertTrue(JournalAudit.objects.filter(action='compte.ouvert', entite_id=response.data['id']).exists())

    def test_ouverture_avec_solde_initial(self):
        response = self.client.post('/api/v1/comptes/', {'client': self.titulaire.id, 'type_compte': 'COURANT', 'solde_initial': '150000'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['solde'], '150000.00')
        depot = Transaction.objects.get(compte_id=response.data['id'])
        self.assertEqual((depot.type_transaction, depot.montant), ('DEPOT', Decimal('150000.00')))
        self.assertTrue(Facture.objects.filter(transaction=depot).exists())
        self.assertIn('150\u00a0000,00\u00a0F\u00a0CFA', JournalAudit.objects.get(action='compte.ouvert').resume)

    def test_solde_initial_negatif_refuse_sans_rien_creer(self):
        response = self.client.post('/api/v1/comptes/', {'client': self.titulaire.id, 'type_compte': 'COURANT', 'solde_initial': '-10'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['solde_initial'], ['Le solde initial ne peut pas être négatif.'])
        self.assertFalse(self.titulaire.comptes.exists())

    def cloturer(self, compte, **data):
        return self.client.post(f'/api/v1/comptes/{compte.id}/cloturer/', data, format='json')

    def test_cloture_si_solde_nul(self):
        compte = self.creer_compte(self.titulaire)
        response = self.cloturer(compte, motif='DEMANDE_CLIENT')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['statut'], 'CLOTURE')
        journal = JournalAudit.objects.get(action='compte.cloture')
        self.assertIn('demande du client', journal.resume)

    def test_motif_obligatoire(self):
        compte = self.creer_compte(self.titulaire)
        response = self.cloturer(compte)
        self.assertEqual(response.status_code, 400)
        self.assertIn('motif', response.data)

    def test_solde_positif_sans_mode_de_restitution_refuse(self):
        compte = self.creer_compte(self.titulaire, solde='50.00')
        response = self.cloturer(compte, motif='DEMANDE_CLIENT')
        self.assertEqual(response.status_code, 400)
        self.assertIn('mode_restitution', response.data)
        compte.refresh_from_db()
        self.assertEqual(compte.statut, 'OUVERT')

    def test_cloture_avec_restitution_par_virement(self):
        compte = self.creer_compte(self.titulaire, solde='7000.00')
        nouveau = self.creer_compte(self.titulaire)
        response = self.cloturer(compte, motif='DEMANDE_CLIENT', mode_restitution='VIREMENT', compte_destinataire=nouveau.id)
        self.assertEqual(response.status_code, 200)
        compte.refresh_from_db()
        nouveau.refresh_from_db()
        self.assertEqual((compte.statut, compte.solde, nouveau.solde), ('CLOTURE', Decimal('0.00'), Decimal('7000.00')))
        self.assertEqual(Transaction.objects.filter(type_transaction='VIREMENT', description='Solde de clôture').count(), 2)

    def test_cloture_avec_remise_en_especes(self):
        compte = self.creer_compte(self.titulaire, solde='2500.00')
        response = self.cloturer(compte, motif='DECISION_BANQUE', mode_restitution='ESPECES')
        self.assertEqual(response.status_code, 200)
        retrait = Transaction.objects.get(type_transaction='RETRAIT')
        self.assertEqual((retrait.montant, retrait.description), (Decimal('2500.00'), 'Solde de clôture (remise en espèces)'))
        self.assertEqual(Facture.objects.filter(transaction=retrait).count(), 1)

    def test_echec_du_virement_annule_tout(self):
        compte = self.creer_compte(self.titulaire, solde='100.00')
        response = self.cloturer(compte, motif='DEMANDE_CLIENT', mode_restitution='VIREMENT', compte_destinataire=compte.id)
        self.assertEqual(response.status_code, 400)
        compte.refresh_from_db()
        self.assertEqual((compte.statut, compte.solde), ('OUVERT', Decimal('100.00')))
        self.assertFalse(Transaction.objects.exists())

    def test_deja_cloture(self):
        compte = self.creer_compte(self.titulaire)
        self.cloturer(compte, motif='DEMANDE_CLIENT')
        self.assertEqual(self.cloturer(compte, motif='DEMANDE_CLIENT').status_code, 400)

    def test_liste_par_client(self):
        self.creer_compte(self.titulaire)
        autre = self.creer_client(self.creer_banque(nom='Autre'), email='b@example.com')
        self.creer_compte(autre)
        response = self.client.get(f'/api/v1/comptes/?client={self.titulaire.id}')
        self.assertEqual(len(response.data), 1)
