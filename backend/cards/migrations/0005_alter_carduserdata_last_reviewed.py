# Generated by Django 4.1.5 on 2023-10-28 13:29

import cards.utils.helpers
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0004_alter_card_back_audio_alter_card_front_audio_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carduserdata',
            name='last_reviewed',
            field=models.DateField(default=cards.utils.helpers.today),
        ),
    ]