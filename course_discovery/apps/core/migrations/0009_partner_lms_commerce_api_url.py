# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-03-14 15:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20181217_1957'),
    ]

    operations = [
        migrations.AddField(
            model_name='partner',
            name='lms_commerce_api_url',
            field=models.URLField(blank=True, max_length=255, null=True, verbose_name='Commerce API URL'),
        ),
    ]
