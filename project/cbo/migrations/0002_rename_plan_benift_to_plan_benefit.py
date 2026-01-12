# Generated manually to fix typo
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cbo', '0001_initial'),
    ]

    operations = [
        # Renomear o campo com typo
        migrations.RenameField(
            model_name='planhasplanbenefit',
            old_name='plan_benift',
            new_name='plan_benefit',
        ),
    ]
