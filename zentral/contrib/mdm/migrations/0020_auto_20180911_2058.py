# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-09-11 20:58
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mdm', '0019_auto_20180828_1212'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='depprofile',
            name='is_multi_user',
        ),
        migrations.AlterField(
            model_name='depprofile',
            name='skip_setup_items',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('AppleID', 'AppleID'), ('Biometric', 'Biometric'), ('Diagnostics', 'Diagnostics'), ('DisplayTone', 'DisplayTone'), ('Location', 'Location'), ('Passcode', 'Passcode'), ('Payment', 'Payment'), ('Privacy', 'Privacy'), ('Restore', 'Restore'), ('Siri', 'Siri'), ('TOS', 'TOS'), ('Zoom', 'Zoom'), ('Android', 'Android'), ('Appearance', 'Appearance'), ('HomeButtonSensitivity', 'HomeButtonSensitivity'), ('iMessageAndFaceTime', 'iMessageAndFaceTime'), ('OnBoarding', 'OnBoarding'), ('ScreenTime', 'ScreenTime'), ('SoftwareUpdate', 'SoftwareUpdate'), ('WatchMigration', 'WatchMigration'), ('FileVault', 'FileVault'), ('iCloudDiagnostics', 'iCloudDiagnostics'), ('iCloudStorage', 'iCloudStorage'), ('Registration', 'Registration'), ('ScreenSaver', 'ScreenSaver'), ('TapToSetup', 'TapToSetup'), ('TVHomeScreenSync', 'TVHomeScreenSync'), ('TVProviderSignIn', 'TVProviderSignIn'), ('TVRoom', 'TVRoom')], max_length=64), editable=False, size=None),
        ),
    ]