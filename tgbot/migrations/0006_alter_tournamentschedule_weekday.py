# Generated by Django 5.0.6 on 2024-09-22 12:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0005_location_weekday_alter_tournamentschedule_location_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournamentschedule',
            name='weekday',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='tgbot.weekday'),
        ),
    ]
