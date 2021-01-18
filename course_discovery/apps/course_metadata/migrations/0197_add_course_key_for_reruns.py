# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-09-19 16:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_metadata', '0196_auto_20190910_1714'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='key_for_reruns',
            field=models.CharField(blank=True, help_text='When making reruns for this course, they will use this key instead of the course key.', max_length=255),
        ),
        migrations.AddField(
            model_name='historicalcourse',
            name='key_for_reruns',
            field=models.CharField(blank=True, help_text='When making reruns for this course, they will use this key instead of the course key.', max_length=255),
        ),
    ]
