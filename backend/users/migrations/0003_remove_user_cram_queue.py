# Generated by Django 4.1.5 on 2023-04-05 10:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_remove_user_skipped_categories_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='cram_queue',
        ),
    ]
