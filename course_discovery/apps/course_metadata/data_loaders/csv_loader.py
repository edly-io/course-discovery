"""
Data loader responsible for creating course and course runs entries in Database
provided a csv containing the required information.
"""
import csv
import logging

from course_discovery.apps.core.utils import serialize_datetime
from course_discovery.apps.course_metadata.data_loaders import AbstractDataLoader
from course_discovery.apps.course_metadata.models import Collaborator, CourseRunPacing, Person, ProgramType
from course_discovery.apps.ietf_language_tags.models import LanguageTag

logger = logging.getLogger(__name__)


class CSVDataLoader(AbstractDataLoader):

    PROGRAM_TYPES = [
        ProgramType.XSERIES,
        ProgramType.MASTERS,
        ProgramType.MICROMASTERS,
        ProgramType.MICROBACHELORS,
        ProgramType.PROFESSIONAL_PROGRAM_WL,
        ProgramType.PROFESSIONAL_CERTIFICATE
    ]

    def __init__(self, partner, api_url=None, max_workers=None, is_threadsafe=False, csv_path=None):
        super().__init__(partner, api_url, max_workers, is_threadsafe)

        try:
            self.reader = csv.DictReader(open(csv_path, 'r'))
        except FileNotFoundError:
            logger.exception(f"Error opening csv file at path {csv_path}")
            raise  # re-raising exception to avoid moving the code flow

    def ingest(self):
        pass

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
            'pacing_type': self.get_pacing_type(data['Course Pacing']),
            'start': self.get_formatted_datetime_string(f"{data['Start Date']}{data['Start Time']}"),
            'end': self.get_formatted_datetime_string(f"{data['End Date']}{data['End Time']}"),
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

    def _update_course_api_request_data(self, data, course, image):
        """
        Create the request data for making a patch call to update the course.

        Arguments:
            * image: base64 encoded image
        """
        subjects = [
            data.get('Primary Subject'),
            data.get('Secondary Subject'),
            data.get('Tertiary Subject')
        ]
        subjects = [subject for subject in subjects if subject]
        collaborators = data['Collaborators'].split(',')
        collaborator_uuids = []
        for collaborator in collaborators:
            collaborator_obj, created = Collaborator.objects.get_or_create(name=collaborator)
            collaborator_uuids.append(collaborator.uuid)
            if created:
                logger.info("Collaborator {} created for course {}".format(collaborator, course.key))

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

            'image': image,
            'prices': pricing,
            'subjects': subjects,
            'collaborators': collaborator_uuids,

            'title': data['Title'],
            'syllabus_raw': data['Syllabus'],
            'level_type': data['Course Level'],
            'outcome': data['What will you learn'],
            'faq': data['Frequently Asked Questions'],
            'video': {'src': data['About Video Link']},
            'prerequisites_raw': data['Prerequisites'],
            'full_description': data['Long Description'],
            'short_description': data['Short Description'],
            'learner_testimonials': data['Learner Testimonials'],
            'additional_information': data['Additional Information'],
        }
        return update_course_data

    def _update_course_run_request_data(self, data, course_run):
        # draft: true
        # external_key: ""
        # rerun: null
        # status: "unpublished"

        content_language = data['Content Language']
        transcript_language = data['Transcript Language'].split(',')
        if not self.verify_languages(content_language, transcript_language):
            raise Exception(f"One or more languages are not valid ietf languages. "
                            f"Content Language: {data['Content Language']}"
                            f"Transcript Languages: {data['Transcript Language']}")

        staff_names_list = data['Staff'].split(',')
        staff_uuids = []

        # TODO: This is a fragile approach. It is possible for two people to have same name within a partner.
        # TODO: CSV would need to provide more information to identify staff members from other than names
        for staff_name in staff_names_list:
            person, created = Person.objects.get_or_create(
                partner=self.partner,
                given_name=staff_name
            )
            staff_uuids.append(person.uuid)
            if created:
                logger.info("Staff with name {} has been created for course run {}".format(
                    staff_name,
                    course_run.key
                ))

        pricing = {
            'verified': data['Verified Price'],  # TODO: temporary value to verified
            # Actual value from course type -> entitlement_tracks -> slugs
        }
        program_type = data['Expected Program Type']

        update_course_run_data = {
            'run_type': course_run.type.uuid,
            'key': course_run.key,

            'prices': pricing,
            'staff': staff_uuids,

            'weeks_to_complete': data['Length'],
            'min_effort': data['Minimum effort'],
            'max_effort': data['Maximum effort'],
            'content_language': data['Content Language'],
            'expected_program_name': data['Expected Program Name'],
            'transcript_languages': data['Transcript Language'].split(','),
            'go_live_date': self.get_formatted_datetime_string(data['Publish Date']),
            'expected_program_type': program_type if program_type in self.PROGRAM_TYPES else None,
            'upgrade_deadline_override': self.get_formatted_datetime_string(
                f"{data['Upgrade Deadline Override Date']}{data['Upgrade Deadline Override Time']}"
            ),
        }
        return update_course_run_data

    def get_formatted_datetime_string(self, date_string):
        """
        Return the datetime string into the desired format %Y-%m-%dT%H:%M:%SZ
        """
        return serialize_datetime(self.parse_date(date_string))

    def get_pacing_type(self, pacing):
        """
        Return appropriate pacing selection against a provided pacing string.
        """
        if pacing:
            pacing = pacing.lower()

        if pacing == 'instructor-paced':
            return CourseRunPacing.Instructor
        elif pacing == 'self-paced':
            return CourseRunPacing.Self
        else:
            return None

    def verify_languages(self, content_language, transcript_languages):
        """
        Given a list of language names, verify that the entries are valid and present
        in the database.
        """
        languages_list = transcript_languages.copy()
        languages_list.append(content_language)
        languages_list = list(set(languages_list))
        for language in languages_list:
            if not LanguageTag.objects.filter(name=language).exists():
                # Returning false instead of creating Language entry because the languages
                # in discovery are per IETF standard.
                return False
        return True
