import json
import logging

from django.core.management import CommandError
from haystack import connections as haystack_connections

from django.core.management.base import BaseCommand
from edly_discovery_app.constants import REQUIRED_MAPPING

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Check if all required mappings are present in the catalog file and Set alieas to latest catalog"
    backends = []

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help="The path to the catalog JSON file (file name should match with indices name)")

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        with open(file_path, 'r') as file:
            catalog_data = json.load(file)

        result = self.check_mappings(catalog_data, REQUIRED_MAPPING)

        style = self.style.SUCCESS if result else self.style.ERROR
        logger.info(style(f'All required mappings present: {result}'))

        if not result:
            return False

        try:
            self.set_alias(file_path.split('/')[-1])
        except Exception as e:
            logger.info(self.style.ERROR(f'Alias are updated to given index: False'))
            raise CommandError(f'ERROR exception : {e}')

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
