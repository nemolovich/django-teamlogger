# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-11 09:06
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('effective_date', models.DateField(default=django.utils.timezone.now)),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('slug', models.SlugField(editable=False)),
                ('criticality', models.CharField(choices=[('L', 'Low'), ('M', 'Medium'), ('H', 'High')], default='L', max_length=1)),
                ('edition_date', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='attachments/%Y/%m/%d/')),
                ('file_name', models.CharField(editable=False, max_length=255)),
                ('file_md5', models.CharField(editable=False, max_length=40, unique=True)),
                ('content_type', models.CharField(editable=False, max_length=100)),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('upload_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='uploads', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=35)),
                ('slug', models.SlugField(editable=False, max_length=40, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='article',
            name='attachments',
            field=models.ManyToManyField(blank=True, to='nouvelles.Attachment'),
        ),
        migrations.AddField(
            model_name='article',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='articles', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='article',
            name='editor',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='editions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='article',
            name='parent_article',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='nouvelles.Article'),
        ),
        migrations.AddField(
            model_name='article',
            name='tags',
            field=models.ManyToManyField(blank=True, to='nouvelles.Tag'),
        ),
    ]
