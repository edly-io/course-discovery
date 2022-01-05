"""
Management commmand to call csv dataloader. see example run syntax
```
./manage.py load_courses_from_csv --partner_code=edx --csv_path=test.csv
```
"""

from django.core.management import BaseCommand, CommandError

from course_discovery.apps.core.models import Partner
from course_discovery.apps.course_metadata.data_loaders.csv_loader import CSVDataLoader


class Command(BaseCommand):
    help = 'Load courses metadata from CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--partner_code',
            dest='partner_code',
            type=str,
            required=True,
            help='The short code of partner which is linked to newly created courses'
        )
        parser.add_argument(
            '--csv_path',
            dest='csv_path',
            type=str,
            required=True,
            help='Path where csv having course meta data is located'
        )

    def handle(self, *args, **options):
        partner_code = options.get('partner_code')
        csv_path = options.get('csv_path')

        try:
            partner = Partner.objects.get(short_code=partner_code)
        except Partner.DoesNotExist:
            raise CommandError('Partner not found with short code [%s]' % partner_code)

        try:
            loader = CSVDataLoader(partner, csv_path=csv_path)
            loader.ingest()
        except Exception as exc:
            raise CommandError('Command failed due to exception in loader. %s' % exc)
