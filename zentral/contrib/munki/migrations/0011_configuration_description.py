# Generated by Django 2.2.24 on 2022-01-20 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('munki', '0010_configuration_collected_condition_keys'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuration',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
