# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-08-28 13:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_metadata', '0110_auto_20180824_1727'),
    ]

    operations = [
        migrations.AddField(
            model_name='pathway',
            name='pathway_type',
            field=models.CharField(choices=[('credit', 'credit'), ('industry', 'industry')], default='credit', max_length=32),
        ),
    ]
