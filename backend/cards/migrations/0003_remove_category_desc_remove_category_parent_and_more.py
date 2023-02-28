# Generated by Django 4.1.5 on 2023-02-28 00:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0002_category_desc_category_parent_category_sib_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='desc',
        ),
        migrations.RemoveField(
            model_name='category',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='category',
            name='sib_order',
        ),
        migrations.AddField(
            model_name='category',
            name='depth',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='numchild',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='category',
            name='path',
            field=models.CharField(default=1, max_length=255, unique=True),
            preserve_default=False,
        ),
    ]