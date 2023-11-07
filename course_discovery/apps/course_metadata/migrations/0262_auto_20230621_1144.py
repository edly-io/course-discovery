# Generated by Django 2.2.16 on 2023-06-21 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_metadata', '0262_auto_20200624_1533'),
    ]

    operations = [
        migrations.AddField(
            model_name='courserun',
            name='course_duration_override',
            field=models.PositiveIntegerField(blank=True, help_text='This field contains override course duration value.', null=True, verbose_name='Course Duration Override'),
        ),
        migrations.AddField(
            model_name='historicalcourserun',
            name='course_duration_override',
            field=models.PositiveIntegerField(blank=True, help_text='This field contains override course duration value.', null=True, verbose_name='Course Duration Override'),
        ),
    ]
