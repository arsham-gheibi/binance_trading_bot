# Generated by Django 4.1.2 on 2022-10-17 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_inspector'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inspector',
            name='code',
            field=models.CharField(max_length=255),
        ),
    ]