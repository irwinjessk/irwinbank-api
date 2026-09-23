from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.api.views.audit import JournalAuditViewSet
from apps.api.views.auth import LogoutView, MeView
from apps.api.views.banques import BanqueViewSet
from apps.api.views.clients import ClientViewSet
from apps.api.views.comptes import CompteViewSet
from apps.api.views.factures import FactureViewSet
from apps.api.views.operations import TransactionViewSet

router = DefaultRouter()
router.register('banques', BanqueViewSet, basename='banque')
router.register('clients', ClientViewSet, basename='client')
router.register('comptes', CompteViewSet, basename='compte')
router.register('transactions', TransactionViewSet, basename='transaction')
router.register('factures', FactureViewSet, basename='facture')
router.register('audit', JournalAuditViewSet, basename='audit')

urlpatterns = [
    path('auth/login', TokenObtainPairView.as_view(), name='login'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('auth/me', MeView.as_view(), name='me'),
    path('', include(router.urls)),
]
