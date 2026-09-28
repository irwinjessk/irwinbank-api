import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def rattacher_clients(apps, schema_editor):
    Client = apps.get_model('clients', 'Client')
    Agence = apps.get_model('banques', 'Agence')
    principales = {agence.banque_id: agence.id for agence in Agence.objects.filter(nom='Agence principale')}
    for client in Client.objects.filter(agence__isnull=True):
        client.agence_id = principales[client.banque_id]
        client.save(update_fields=['agence'])


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('banques', '0002_agence'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='agence',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='clients', to='banques.agence'),
        ),
        migrations.AddField(
            model_name='client',
            name='conseiller',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clients_suivis', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(rattacher_clients, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='client',
            name='agence',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='clients', to='banques.agence'),
        ),
    ]
