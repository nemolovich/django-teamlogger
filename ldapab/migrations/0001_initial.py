# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-26 11:49
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='DirectoryInfo',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='directory_info', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('source', models.CharField(max_length=100)),
            ],
        ),
    ]
