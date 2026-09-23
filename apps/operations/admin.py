from django.contrib import admin

from apps.operations.models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date_transaction', 'type_transaction', 'sens', 'montant', 'compte')
    list_filter = ('type_transaction', 'sens')
    search_fields = ('description', 'compte__numero_compte')
