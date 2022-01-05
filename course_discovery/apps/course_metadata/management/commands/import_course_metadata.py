"""
Management command to import, create, and/or update course and course run information for
executive education courses.
"""
import logging

from django.core.management import BaseCommand

from course_discovery.apps.core.models import Partner
from course_discovery.apps.course_metadata.data_loaders.csv_loader import CSVDataLoader

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import course and course run information from a CSV available on a provided csv path.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--partner_code',
            help='The short code for a specific partner to import courses to, defaults to "edx".',
            default='edx',
            type=str,
        )
        parser.add_argument(
            '--csv_path',
            help='Path to the CSV file',
            type=str,
            required=True
        )

    def handle(self, *args, **options):

        partner_short_code = options.get('partner_code')
        csv_path = options.get('csv_path')
        try:
            partner = Partner.objects.get(short_code=partner_short_code)
        except Partner.DoesNotExist:
            logger.exception("Unable to locate partner with code {}".format(partner_short_code))
            return

        try:
            loader = CSVDataLoader(partner, csv_path=csv_path)
        except FileNotFoundError:
            logger.exception("Unable to open csv file located at path {}".format(csv_path))
        else:
            logger.info("Starting CSV loader import flow for partner {}".format(partner_short_code))
            loader.ingest()
            logger.info("CSV loader import flow completed.")
