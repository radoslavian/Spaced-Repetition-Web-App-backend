# Generated by Django 4.1.5 on 2023-03-30 19:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0005_rename_all_repetitions_reviewdatasm2_total_reviews'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Template',
            new_name='CardTemplate',
        ),
    ]