# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-11-01 19:34
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publisher', '0084_make_course_has_ofac_restrictions_nullable'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='has_ofac_restrictions',
        ),
        migrations.RemoveField(
            model_name='historicalcourse',
            name='has_ofac_restrictions',
        ),
    ]
