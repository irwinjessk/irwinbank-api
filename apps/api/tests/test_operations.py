from decimal import Decimal

from apps.api.tests.support import ApiTestCase
from apps.audit.models import JournalAudit
from apps.facturation.models import Facture
from apps.operations.models import Transaction


class OperationsApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        banque = self.creer_banque()
        self.source = self.creer_compte(self.creer_client(banque, email='a@example.com'), solde='100.00')
        self.cible = self.creer_compte(self.creer_client(banque, email='b@example.com'))

    def poster(self, **data):
        return self.client.post('/api/v1/transactions/', data, format='json')

    def test_depot_credite_et_facture(self):
        response = self.poster(type_transaction='DEPOT', compte=self.source.id, montant='25.00')
        self.assertEqual(response.status_code, 201)
        self.source.refresh_from_db()
        self.assertEqual(self.source.solde, Decimal('125.00'))
        self.assertEqual(Facture.objects.count(), 1)
        self.assertEqual(JournalAudit.objects.filter(action='transaction.deposee').count(), 1)

    def test_retrait_refuse_si_solde_insuffisant(self):
        response = self.poster(type_transaction='RETRAIT', compte=self.source.id, montant='500.00')
        self.assertEqual(response.status_code, 400)
        self.source.refresh_from_db()
        self.assertEqual(self.source.solde, Decimal('100.00'))
        self.assertEqual(Transaction.objects.count(), 0)

    def test_virement_ecrit_deux_lignes_liees(self):
        response = self.poster(
            type_transaction='VIREMENT', compte=self.source.id,
            compte_contrepartie=self.cible.id, montant='40.00',
        )
        self.assertEqual(response.status_code, 201)
        self.source.refresh_from_db()
        self.cible.refresh_from_db()
        self.assertEqual(self.source.solde, Decimal('60.00'))
        self.assertEqual(self.cible.solde, Decimal('40.00'))
        references = set(Transaction.objects.values_list('reference_virement', flat=True))
        self.assertEqual(len(references), 1)

    def test_virement_vers_le_meme_compte_refuse(self):
        response = self.poster(
            type_transaction='VIREMENT', compte=self.source.id,
            compte_contrepartie=self.source.id, montant='10.00',
        )
        self.assertEqual(response.status_code, 400)

    def test_montant_negatif_refuse(self):
        response = self.poster(type_transaction='DEPOT', compte=self.source.id, montant='-5')
        self.assertEqual(response.status_code, 400)

    def test_filtre_par_type(self):
        self.poster(type_transaction='DEPOT', compte=self.source.id, montant='5.00')
        self.poster(type_transaction='RETRAIT', compte=self.source.id, montant='5.00')
        response = self.client.get('/api/v1/transactions/?type=RETRAIT')
        self.assertEqual(len(response.data), 1)
