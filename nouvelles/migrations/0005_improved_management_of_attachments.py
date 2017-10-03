# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-24 09:14
from __future__ import unicode_literals

import hashlib

import django.db.models.deletion
from django.core.files import File
from django.db import migrations, models

from nouvelles import models as nouvelles_models
from nouvelles.utils import sizeof_fmt


def forwards_func(apps, schema_editor):
    Attachment = apps.get_model("nouvelles", "Attachment")
    db_alias = schema_editor.connection.alias

    for attach in Attachment.objects.using(db_alias).all():
        for article in attach.article_old.all():
            try:
                new_attach = Attachment(article=article, upload_by=attach.upload_by, upload_date=attach.upload_date)
                file = File(attach.file.file, attach.name)
                new_attach.name = attach.name
                new_attach.size = sizeof_fmt(file.size)
                new_attach.file.save(attach.name, file)
            except FileNotFoundError:
                # If attachment is not found on the disk, it will be ignored
                pass
        attach.delete()


def reverse_func(apps, schema_editor):
    def compute_file_md5(file):
        hash_md5 = hashlib.md5()
        for chunk in file.chunks():
            hash_md5.update(chunk)
        return hash_md5.hexdigest()

    Attachment = apps.get_model("nouvelles", "Attachment")
    db_alias = schema_editor.connection.alias

    for attach in Attachment.objects.using(db_alias).all():
        attach.file_md5 = compute_file_md5(attach.file)
        attach.content_type = "Undefined"
        attach.article_old.add(attach.article)
        attach.save()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('nouvelles', '0004_adding_user_profile'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attachment',
            old_name='file_name',
            new_name='name',
        ),
        migrations.AlterField(
            model_name='attachment',
            name='file',
            field=models.FileField(upload_to=nouvelles_models.attachment_upload_path),
        ),

        # Add temporary fields changes for data migration
        migrations.AlterField(
            model_name='attachment',
            name='file_md5',
            field=models.CharField(max_length=40, unique=True, blank=True, null=True)
        ),
        migrations.AlterField(
            model_name='attachment',
            name='content_type',
            field=models.CharField(max_length=100, editable=False, blank=True, null=True)
        ),
        migrations.AlterField(
            model_name='article',
            name='attachments',
            field=models.ManyToManyField(blank=True, related_name='article_old', to='nouvelles.Attachment'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='article',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments_new',
                                    to='nouvelles.Article', null=True, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attachment',
            name='size',
            field=models.CharField(max_length=20, editable=False, null=True, blank=True),
            preserve_default=False,
        ),

        # Run files migration
        migrations.RunPython(forwards_func, reverse_func, atomic=True),

        # Remove unnecessary fields
        migrations.RemoveField(
            model_name='article',
            name='attachments'
        ),
        migrations.RemoveField(
            model_name='attachment',
            name='file_md5',
        ),
        migrations.RemoveField(
            model_name='attachment',
            name='content_type',
        ),
        migrations.AlterField(
            model_name='attachment',
            name='article',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments',
                                    to='nouvelles.Article'),
            preserve_default=False
        ),
        migrations.AlterField(
            model_name='attachment',
            name='size',
            field=models.CharField(max_length=20, editable=False),
            preserve_default=False,
        ),
    ]