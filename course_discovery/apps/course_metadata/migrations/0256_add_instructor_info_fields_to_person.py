# Generated by Django 2.2.16 on 2021-02-18 08:09

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_metadata', '0255_add_designation_and_profile_image_url_to_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='marketing_id',
            field=models.PositiveIntegerField(blank=True, help_text='This field contains instructor post ID from wordpress.', null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='marketing_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='phone_number',
            field=models.CharField(blank=True, max_length=50, null=True, validators=[django.core.validators.RegexValidator(message='Phone number can only contain numbers.', regex='^\\+?1?\\d*$')]),
        ),
        migrations.AddField(
            model_name='person',
            name='website',
            field=models.URLField(blank=True, null=True),
        ),
    ]
