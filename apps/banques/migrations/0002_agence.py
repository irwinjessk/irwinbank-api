import django.db.models.deletion
from django.db import migrations, models


def creer_agences_principales(apps, schema_editor):
    Banque = apps.get_model('banques', 'Banque')
    Agence = apps.get_model('banques', 'Agence')
    for banque in Banque.objects.all():
        Agence.objects.get_or_create(banque=banque, nom='Agence principale', defaults={'ville': banque.ville})


class Migration(migrations.Migration):

    dependencies = [
        ('banques', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Agence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=120)),
                ('ville', models.CharField(max_length=80)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('actif', models.BooleanField(default=True)),
                ('banque', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='agences', to='banques.banque')),
            ],
            options={
                'db_table': 'agence',
                'ordering': ['banque__nom', 'nom'],
                'constraints': [models.UniqueConstraint(fields=('banque', 'nom'), name='agence_nom_unique_par_banque')],
            },
        ),
        migrations.RunPython(creer_agences_principales, migrations.RunPython.noop),
    ]
