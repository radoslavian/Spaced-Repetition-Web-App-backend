# Generated by Django 4.1.5 on 2025-03-01 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0005_alter_carduserdata_last_reviewed'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='sha1_digest',
            field=models.CharField(default='869ed35b9a2c91a105897f599d1d23ea2e782f75', max_length=40, unique=True),
        ),
    ]
