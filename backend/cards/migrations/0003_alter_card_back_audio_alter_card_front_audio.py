# Generated by Django 4.1.5 on 2023-09-21 21:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='back_audio',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cards_back', to='cards.sound'),
        ),
        migrations.AlterField(
            model_name='card',
            name='front_audio',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cards_front', to='cards.sound'),
        ),
    ]
