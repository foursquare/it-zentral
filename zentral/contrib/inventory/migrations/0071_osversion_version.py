# Generated by Django 3.2.12 on 2022-05-02 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0070_ec2_instance_tags_on_delete_cascade'),
    ]

    operations = [
        migrations.AddField(
            model_name='osversion',
            name='version',
            field=models.TextField(blank=True, null=True),
        ),
    ]
