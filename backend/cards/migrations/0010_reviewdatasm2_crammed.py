# Generated by Django 4.1.5 on 2023-04-05 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0009_card_created_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewdatasm2',
            name='crammed',
            field=models.BooleanField(default=False),
        ),
    ]