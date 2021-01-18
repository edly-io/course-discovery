# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-10-08 18:33
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('course_metadata', '0202_backpopulatecoursetypeconfig'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseruntype',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='coursetype',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='historicalcourseruntype',
            name='uuid',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='historicalcoursetype',
            name='uuid',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, verbose_name='UUID'),
        ),
    ]
