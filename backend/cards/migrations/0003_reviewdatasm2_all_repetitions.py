# Generated by Django 4.1.5 on 2023-03-24 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewdatasm2',
            name='all_repetitions',
            field=models.IntegerField(default=1),
        ),
    ]