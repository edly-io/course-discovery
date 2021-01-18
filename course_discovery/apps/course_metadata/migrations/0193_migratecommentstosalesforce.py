# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-08-29 13:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_add_case_record_type_id'),
        ('course_metadata', '0192_draft_version_set_null'),
    ]

    operations = [
        migrations.CreateModel(
            name='MigrateCommentsToSalesforce',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orgs', sortedm2m.fields.SortedManyToManyField(blank=True, help_text=None, to='course_metadata.Organization')),
                ('partner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Partner')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
