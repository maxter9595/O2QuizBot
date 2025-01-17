# Generated by Django 5.0.6 on 2024-09-22 15:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0006_alter_tournamentschedule_weekday'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournamentschedule',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='questions_images/'),
        ),
        migrations.AlterField(
            model_name='tournamentschedule',
            name='weekday',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tgbot.weekday'),
        ),
    ]
