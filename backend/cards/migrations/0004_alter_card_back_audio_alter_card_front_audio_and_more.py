# Generated by Django 4.1.5 on 2023-09-22 14:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0003_alter_card_back_audio_alter_card_front_audio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='back_audio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cards_back', to='cards.sound'),
        ),
        migrations.AlterField(
            model_name='card',
            name='front_audio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cards_front', to='cards.sound'),
        ),
        migrations.AlterField(
            model_name='card',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='cards', to='cards.cardtemplate'),
        ),
    ]
