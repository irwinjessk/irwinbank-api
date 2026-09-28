from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.api.views.agences import AgenceViewSet
from apps.api.views.audit import JournalAuditViewSet
from apps.api.views.auth import LogoutView, MeView
from apps.api.views.banques import BanqueViewSet
from apps.api.views.clients import ClientViewSet
from apps.api.views.comptes import CompteViewSet
from apps.api.views.dashboard import DashboardView
from apps.api.views.espace_client import (
    ActivationEspaceView,
    EspaceCompteViewSet,
    EspaceFactureViewSet,
    EspaceMotDePasseView,
    EspaceProfilView,
    EspaceTransactionViewSet,
)
from apps.api.views.factures import FactureViewSet
from apps.api.views.operations import TransactionViewSet

router = DefaultRouter()
router.register('banques', BanqueViewSet, basename='banque')
router.register('agences', AgenceViewSet, basename='agence')
router.register('clients', ClientViewSet, basename='client')
router.register('comptes', CompteViewSet, basename='compte')
router.register('transactions', TransactionViewSet, basename='transaction')
router.register('factures', FactureViewSet, basename='facture')
router.register('audit', JournalAuditViewSet, basename='audit')

espace_router = DefaultRouter()
espace_router.include_root_view = False
espace_router.register('comptes', EspaceCompteViewSet, basename='espace-compte')
espace_router.register('transactions', EspaceTransactionViewSet, basename='espace-transaction')
espace_router.register('factures', EspaceFactureViewSet, basename='espace-facture')

urlpatterns = [
    path('auth/login', TokenObtainPairView.as_view(), name='login'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('auth/me', MeView.as_view(), name='me'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('espace-client/activation/', ActivationEspaceView.as_view(), name='espace-activation'),
    path('espace-client/profil/', EspaceProfilView.as_view(), name='espace-profil'),
    path('espace-client/mot-de-passe/', EspaceMotDePasseView.as_view(), name='espace-mot-de-passe'),
    path('espace-client/', include(espace_router.urls)),
    path('', include(router.urls)),
]
