# Generated by Django 2.2.16 on 2020-10-19 19:13

import course_discovery.apps.course_metadata.utils
from django.db import migrations, models
import stdimage.models


class Migration(migrations.Migration):

    dependencies = [
        ('course_metadata', '0257_auto_20200813_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalprogram',
            name='card_image',
            field=models.TextField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='program',
            name='card_image',
            field=stdimage.models.StdImageField(blank=True, null=True, upload_to=course_discovery.apps.course_metadata.utils.UploadToFieldNamePath(path='media/programs/card_images/', populate_from='uuid')),
        ),
    ]
