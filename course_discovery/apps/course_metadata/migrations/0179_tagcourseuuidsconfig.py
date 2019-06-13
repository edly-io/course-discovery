# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-06-13 16:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_metadata', '0178_external-key'),
    ]

    operations = [
        migrations.CreateModel(
            name='TagCourseUuidsConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.TextField(default=None, verbose_name='Tag')),
                ('course_uuids', models.TextField(default=None, verbose_name='Course UUIDs')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
