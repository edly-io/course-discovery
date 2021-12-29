"""
Data loader responsible for creating course and course runs entries in Database
provided a csv containing the required information.
"""
import csv
import logging

from course_discovery.apps.core.utils import serialize_datetime
from course_discovery.apps.course_metadata.data_loaders import AbstractDataLoader
from course_discovery.apps.course_metadata.models import CourseRunPacing

logger = logging.getLogger(__name__)


class CSVDataLoader(AbstractDataLoader):

    def __init__(self, partner, api_url=None, max_workers=None, is_threadsafe=False, csv_path=None):
        super().__init__(partner, api_url, max_workers, is_threadsafe)

        try:
            self.reader = csv.DictReader(open(csv_path, 'r'))
        except FileNotFoundError:
            logger.exception(f"Error opening csv file at path {csv_path}")
            raise  # re-raising exception to avoid moving the code flow

    def _create_course_api_request_data(self, data, enrollment_type_uuid, course_run_type_uuid):
        """
        Given a data dictionary, return a reduced data representation in dict
        which will be used as course api request data.

        TODO: update the keys in data when the actual CSV structure is confirmed.
        """
        pricing = {
            'verified': data['Verified Price'],  # TODO: temporary value to verified
            # Actual value from course type -> entitlement_tracks -> slugs
        }

        # TODO: make appropriate timezone adjustment when it is confirmed if time values are in EST or UTC
        course_run_creation_fields = {
            'pacing_type': CourseRunPacing.Self if 'Self-' in data['Course Pacing'] else CourseRunPacing.Instructor,
            'start': serialize_datetime(self.parse_date(f"{data['Start Date']}{data['Start Time']}")),
            'end': serialize_datetime(self.parse_date(f"{data['End Date']}{data['End Time']}")),
            'run_type': course_run_type_uuid,
            'prices': pricing
        }
        return {
            'org': data['Organization'],
            'title': data['Title'],
            'number': data['Number'],
            'type': enrollment_type_uuid,
            'prices': pricing,
            'course_run': course_run_creation_fields
        }

    def _update_course_api_request_data(self, data, course, collaborators, image):
        """
        Create the request data for making a patch call to update the course.

        Arguments:
            * collaborators(list): list of collaborator uuids
            * image: base64 encoded image
        """
        subjects = [
            data.get('Primary Subject'),
            data.get('Secondary Subject'),
            data.get('Tertiary Subject')
        ]
        subjects = [subject for subject in subjects if subject]
        pricing = {
            'verified': data['Verified Price'],  # TODO: temporary value to verified
            # Actual value from course type -> entitlement_tracks -> slugs
        }
        # draft: true

        update_course_data = {
            'uuid': course.uuid,
            'key': course.key,
            'url_slug': course.url_slug,
            'type': course.type.uuid,

            'title': data['Title'],
            'additional_information': data['Additional Information'],
            'short_description': data['Short Description'],
            'full_description': data['Long Description'],
            'faq': data['Frequently Asked Questions'],
            'learner_testimonials': data['Learner Testimonials'],
            'outcome': data['What will you learn'],
            'prerequisites_raw': data['Prerequisites'],
            'prices': pricing,

            'syllabus_raw': data['Syllabus'],
            'level_type': data['Course Level'],
            'subjects': subjects,
            'collaborators': collaborators,

            'image': image,
            'video': {'src': data['About Video Link']},
        }
        return update_course_data
