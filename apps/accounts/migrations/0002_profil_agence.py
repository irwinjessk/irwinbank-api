import django.db.models.deletion
from django.db import migrations, models


def rattacher_agents(apps, schema_editor):
    Profil = apps.get_model('accounts', 'Profil')
    Agence = apps.get_model('banques', 'Agence')
    for profil in Profil.objects.filter(role='AGENT', agence__isnull=True, banque__isnull=False):
        profil.agence = Agence.objects.get(banque_id=profil.banque_id, nom='Agence principale')
        profil.save(update_fields=['agence'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('banques', '0002_agence'),
    ]

    operations = [
        migrations.AddField(
            model_name='profil',
            name='agence',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='agents', to='banques.agence'),
        ),
        migrations.RunPython(rattacher_agents, migrations.RunPython.noop),
    ]
