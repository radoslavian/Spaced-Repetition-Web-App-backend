# Generated by Django 4.1.5 on 2023-04-05 11:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_remove_user_cram_queue'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='cards_review_data',
            new_name='memorized_cards',
        ),
    ]