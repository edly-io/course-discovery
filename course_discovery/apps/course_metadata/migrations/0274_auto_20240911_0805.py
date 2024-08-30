# Generated by Django 2.2.16 on 2024-09-11 08:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_metadata', '0273_auto_20240910_1605'),
    ]

    operations = [
        migrations.AddField(
            model_name='courserun',
            name='course_language',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Language of the course run'),
        ),
        migrations.AddField(
            model_name='historicalcourserun',
            name='course_language',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Language of the course run'),
        ),
    ]
