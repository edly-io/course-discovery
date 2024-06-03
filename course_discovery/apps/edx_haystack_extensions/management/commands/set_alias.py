import json
import logging

from django.core.management import CommandError
from haystack import connections as haystack_connections

from django.core.management.base import BaseCommand


logger = logging.getLogger(__name__)


required_mappings = {
    "modelresult": {
        "properties": {
            "aggregation_key": {"type": "string", "index": "not_analyzed"},
            "announcement": {"type": "date", "format": "dateOptionalTime"},
            "authoring_organization_bodies": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "authoring_organization_uuids": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "authoring_organizations": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "authoring_organizations_autocomplete": {"type": "string", "boost": 25.0, "index_analyzer": "ngram_analyzer", "search_analyzer": "snowball_with_synonyms"},
            "authoring_organizations_exact": {"type": "string", "index": "not_analyzed"},
            "availability": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "average_rating": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "bio": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "bio_language": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "card_image_url": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "content_type": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "content_type_exact": {"type": "string", "index": "not_analyzed"},
            "course_duration_override": {"type": "long"},
            "course_key": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "course_runs": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "created": {"type": "date", "format": "dateOptionalTime"},
            "credit_backing_organizations": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "credit_backing_organizations_exact": {"type": "string", "index": "not_analyzed"},
            "designation": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "django_ct": {"type": "string", "index": "not_analyzed", "include_in_all": False},
            "django_id": {"type": "string", "index": "not_analyzed", "include_in_all": False},
            "end": {"type": "date", "format": "dateOptionalTime"},
            "enrollment_end": {"type": "date", "format": "dateOptionalTime"},
            "enrollment_start": {"type": "date", "format": "dateOptionalTime"},
            "expected_learning_items": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "featured": {"type": "boolean"},
            "first_enrollable_paid_seat_price": {"type": "long"},
            "first_enrollable_paid_seat_sku": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "full_description": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "full_name": {"type": "string", "index": "not_analyzed"},
            "get_profile_image_url": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "go_live_date": {"type": "date", "format": "dateOptionalTime"},
            "has_enrollable_paid_seats": {"type": "boolean"},
            "has_enrollable_seats": {"type": "boolean"},
            "hidden": {"type": "boolean"},
            "hidden_exact": {"type": "boolean"},
            "id": {"type": "string"},
            "image_url": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "is_current_and_still_upgradeable": {"type": "boolean"},
            "is_marketing_price_hidden": {"type": "boolean"},
            "is_marketing_price_set": {"type": "boolean"},
            "is_program_eligible_for_one_click_purchase": {"type": "boolean"},
            "key": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "language": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "language_exact": {"type": "string", "index": "not_analyzed"},
            "languages": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "level_type": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "level_type_exact": {"type": "string", "index": "not_analyzed"},
            "license": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "license_exact": {"type": "string", "index": "not_analyzed"},
            "logo_image_urls": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "marketing_id": {"type": "long"},
            "marketing_price_value": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "marketing_url": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "max_effort": {"type": "long"},
            "max_hours_effort_per_week": {"type": "long"},
            "min_effort": {"type": "long"},
            "min_hours_effort_per_week": {"type": "long"},
            "mobile_available": {"type": "boolean"},
            "mobile_available_exact": {"type": "boolean"},
            "modified": {"type": "date", "format": "dateOptionalTime"},
            "number": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "org": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "organizations": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "organizations_exact": {"type": "string", "index": "not_analyzed"},
            "outcome": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "pacing_type": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "pacing_type_exact": {"type": "string", "index": "not_analyzed"},
            "paid_seat_enrollment_end": {"type": "date", "format": "dateOptionalTime"},
            "partner": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "partner_exact": {"type": "string", "index": "not_analyzed"},
            "position": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "prerequisites": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "prerequisites_exact": {"type": "string", "index": "not_analyzed"},
            "program_types": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "published": {"type": "boolean"},
            "published_exact": {"type": "boolean"},
            "salutation": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "search_card_display": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "seat_types": {"type": "string", "analyzer": "snowball_with_synonyms"},
            "seat_types_exact": {"type": "string", "index": "not_analyzed"}
        }
    }
}


class Command(BaseCommand):
    help = "Check if all required mappings are present in the catalog file and Set alieas to latest catalog"
    backends = []

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help="The path to the catalog JSON file")

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        with open(file_path, 'r') as file:
            catalog_data = json.load(file)

        result = self.check_mappings(catalog_data, required_mappings)

        style = self.style.SUCCESS if result else self.style.ERROR
        logger.info(style(f'All required mappings present: {result}'))

        if not result:
            return False

        try:
            self.set_alias(file_path.split('/')[-1])
        except Exception as e:
            logger.info(self.style.ERROR(f'Alias are updated to given index: False'))
            raise CommandError(f'ERROR exceptio : {e}')

        logger.info(style(f'Alias are updated to given index: True'))


    def check_mappings(self, catalog_data, required_mappings):
        catalog_key = list(catalog_data.keys())[0]
        catalog_mappings = catalog_data[catalog_key]['mappings']
        error_style = self.style.ERROR
        
        for key, value in required_mappings.items():
            if key not in catalog_mappings:
                logger.info(error_style(f'Mapping does not exist for key" {key}'))
                return False

            for prop, prop_value in value['properties'].items():
                if prop not in catalog_mappings[key]['properties']:
                    logger.info(error_style(f'Property does not exist: "{prop}"'))
                    return False

                prop_name = catalog_mappings[key]['properties'][prop]
                if prop_name != prop_value:
                    logger.info(error_style(f'Invalid value of property "{prop}": "{prop_name}"'))
                    return False
        return True
    

    def set_alias(self, index_name):
        self.backends = list(haystack_connections.connections_info.keys())

        for backend_name in self.backends:
            connection = haystack_connections[backend_name]
            backend = connection.get_backend()
            alias = backend.index_name
            body = {
                'actions': [
                    {'remove': {'alias': alias, 'index': '*'}},
                    {'add': {'alias': alias, 'index': index_name}},
                ]
            }
            backend.conn.indices.update_aliases(body)
