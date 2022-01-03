"""
Data loader responsible for creating course and course runs entries in Database
provided a csv containing the required information.
"""
import csv
import logging

from django.urls import reverse

from course_discovery.apps.core.utils import serialize_datetime
from course_discovery.apps.course_metadata.data_loaders import AbstractDataLoader
from course_discovery.apps.course_metadata.models import (
    Collaborator, Course, CourseRun, CourseRunPacing, CourseRunType, CourseType, Organization, Person, ProgramType
)
from course_discovery.apps.course_metadata.utils import download_and_save_course_image
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
            logger.exception("Error opening csv file at path {}".format(csv_path))
            raise  # re-raising exception to avoid moving the code flow

    def transform_dict_keys(self, data):
        """
        Given a data dictionary, return a new dict that has its keys transformed to
        snake case. For example, Enrollment Track becomes enrollment_track.

        Each key is stripped of whitespaces around the edges, converted to lower case,
        and has internal spaces converted to _. This convention removes the dependency on CSV
        headers format(Enrollment Track vs Enrollment track) and makes code flexible to ignore
        any case sensitivity, among other things.
        """
        transformed_dict = {}
        for key, value in data.items():
            updated_key = key.strip().lower().replace(' ', '_')
            transformed_dict[updated_key] = value
        return transformed_dict

    def ingest(self):
        logger.info("Initiating CSV data loader flow")
        for row in self.reader:

            row = self.transform_dict_keys(row)
            course_title = row['title']
            org_key = row['organization']

            logger.info('Starting data import flow for {}'.format(course_title))

            if not Organization.objects.filter(key=org_key).exists():
                logger.error("Organization {} does not exist in database. Skipping CSV loader for course {}".format(
                    org_key,
                    course_title
                ))
                continue

            try:
                course_type = CourseType.objects.get(name=row['course_enrollment_track'])
                course_run_type = CourseRunType.objects.get(name=row['course_run_enrollment_track'])
            except CourseType.DoesNotExist:
                logger.exception("CourseType {} does not exist in the database.".format(
                    row['course_enrollment_track']
                ))
                continue
            except CourseRunType.DoesNotExist:
                logger.exception("CourseRunType {} does not exist in the database.".format(
                    row['course_run_enrollment_track']
                ))
                continue

            course_key = self.get_course_key(org_key, row['number'])

            try:
                # TODO: to confirm if draft based filtering is necessary or not
                course = Course.everything.get(key=course_key, partner=self.partner)
                course_run = CourseRun.everything.get(course=course)
                logger.info("Course {} located in the database.".format(course_key))
            except Course.DoesNotExist:
                logger.info("Course with key {} not found in database, creating the course.".format(course_key))
                try:
                    _ = self._create_course(row, course_type.uuid, course_run_type.uuid)
                except Exception:  # pylint: disable=broad-except
                    logger.exception("Error occurred when attempting to create a new course against key {}".format(
                        course_key
                    ))
                    continue
                course = Course.everything.get(key=course_key, partner=self.partner)
                course_run = CourseRun.everything.get(course=course)

            try:
                self._update_course(row, course)
                self._update_course_run(row, course_run)
                download_and_save_course_image(course, row['image'])
                logger.info("Course and course run updated successfully")
            except Exception:  # pylint: disable=broad-except
                logger.exception("Error occurred while updating course and course run")
                continue

    def _create_course_api_request_data(self, data, course_type_uuid, course_run_type_uuid):
        """
        Given a data dictionary, return a reduced data representation in dict
        which will be used as course api request data.

        TODO: update the keys in data when the actual CSV structure is confirmed.
        """
        pricing = {
            'verified': data['verified_price'],  # TODO: temporary value to verified
            # Actual value from course type -> entitlement_tracks -> slugs
        }

        # TODO: make appropriate timezone adjustment when it is confirmed if time values are in EST or UTC
        course_run_creation_fields = {
            'pacing_type': self.get_pacing_type(data['course_pacing']),
            'start': self.get_formatted_datetime_string(f"{data['start_date']} {data['start_time']}"),
            'end': self.get_formatted_datetime_string(f"{data['end_date']} {data['end_time']}"),
            'run_type': str(course_run_type_uuid),
            'prices': pricing
        }
        return {
            'org': data['organization'],
            'title': data['title'],
            'number': data['number'],
            'type': str(course_type_uuid),
            'prices': pricing,
            'course_run': course_run_creation_fields
        }

    def _update_course_api_request_data(self, data, course):
        """
        Create the request data for making a patch call to update the course.
        """
        subjects = [
            data.get('primary_subject'),
            data.get('secondary_subject'),
            data.get('tertiary_subject')
        ]
        subjects = [subject for subject in subjects if subject]
        subjects = list(set(subjects))

        collaborators = data['collaborators'].split(',')
        collaborators = [collaborator for collaborator in collaborators if collaborator.strip()]
        collaborator_uuids = []
        for collaborator in collaborators:
            collaborator_obj, created = Collaborator.objects.get_or_create(name=collaborator)
            collaborator_uuids.append(str(collaborator_obj.uuid))
            if created:
                logger.info("Collaborator {} created for course {}".format(collaborator, course.key))

        pricing = {
            'verified': data['verified_price'],  # TODO: temporary value to verified
            # Actual value from course type -> entitlement_tracks -> slugs
        }

        update_course_data = {
            'uuid': str(course.uuid),
            'key': course.key,
            'url_slug': course.url_slug,
            'type': str(course.type.uuid),
            'draft': False,

            'prices': pricing,
            'subjects': subjects,
            'collaborators': collaborator_uuids,

            'title': data['title'],
            'syllabus_raw': data['syllabus'],
            'level_type': data['course_level'],
            'outcome': data['what_will_you_learn'],
            'faq': data['frequently_asked_questions'],
            'video': {'src': data['about_video_link']},
            'prerequisites_raw': data['prerequisites'],
            'full_description': data['long_description'],
            'short_description': data['short_description'],
            'learner_testimonials': data['learner_testimonials'],
            'additional_information': data['additional_information'],
        }
        return update_course_data

    def _update_course_run_request_data(self, data, course_run):
        # draft: true
        # external_key: ""
        # rerun: null
        # status: "unpublished"

        content_language = data['content_language']
        transcript_language = data['transcript_language'].split(',')
        if not self.verify_languages(content_language, transcript_language):
            raise Exception(f"One or more languages are not valid ietf languages. "
                            f"Content Language: {data['content_language']},"
                            f"Transcript Languages: {data['transcript_language']}")

        staff_names_list = data['staff'].split(',')
        staff_names_list = [staff_name for staff_name in staff_names_list if staff_name.strip()]
        staff_uuids = []

        # TODO: This is a fragile approach. It is possible for two people to have same name within a partner.
        # TODO: CSV would need to provide more information to identify staff members from other than names
        for staff_name in staff_names_list:
            person, created = Person.objects.get_or_create(
                partner=self.partner,
                given_name=staff_name
            )
            staff_uuids.append(str(person.uuid))
            if created:
                logger.info("Staff with name {} has been created for course run {}".format(
                    staff_name,
                    course_run.key
                ))

        pricing = {
            'verified': data['verified_price'],  # TODO: temporary value to verified
            # Actual value from course type -> entitlement_tracks -> slugs
        }
        program_type = data['expected_program_type']

        update_course_run_data = {
            'run_type': str(course_run.type.uuid),
            'key': course_run.key,
            'draft': False,

            'prices': pricing,
            'staff': staff_uuids,

            'weeks_to_complete': data['length'],
            'min_effort': data['minimum_effort'],
            'max_effort': data['maximum_effort'],
            'content_language': data['content_language'],
            'expected_program_name': data['expected_program_name'],
            'transcript_languages': data['transcript_language'].split(','),
            'go_live_date': self.get_formatted_datetime_string(data['publish_date']),
            'expected_program_type': program_type if program_type in self.PROGRAM_TYPES else None,
            'upgrade_deadline_override': self.get_formatted_datetime_string(
                f"{data['upgrade_deadline_override_date']} {data['upgrade_deadline_override_time']}"
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
            if not LanguageTag.objects.filter(name=language.lower()).exists():
                # Returning false instead of creating Language entry because the languages
                # in discovery are per IETF standard.
                return False
        return True

    def _create_course(self, data, course_type_uuid, course_run_type_uuid):
        """
        Make a course entry through course api.

        (Question: Should api call be made via client or by direct call of method of ViewSet?)
        """
        request_data = self._create_course_api_request_data(data, course_type_uuid, course_run_type_uuid)
        # TODO: Add proper discovery base url settings
        response = self.api_client.request(
            'POST',
            'http://localhost:18381' + reverse('api:v1:course-list'),
            json=request_data
        )
        response.raise_for_status()
        return response.json()

    def _update_course(self, data, course):
        """
        Update the course data.

        (Question: Should api call be made via client or by direct call of method of ViewSet?)
        """
        request_data = self._update_course_api_request_data(data, course)
        response = self.api_client.request(
            'PATCH',
            'http://localhost:18381' + reverse('api:v1:course-detail', kwargs={'key': course.key}),
            json=request_data)
        response.raise_for_status()
        return response.json()

    def _update_course_run(self, data, course_run):
        """
        Update the course data.

        (Question: Should api call be made via client or by direct call of method of ViewSet?)
        """
        request_data = self._update_course_run_request_data(data, course_run)
        response = self.api_client.request(
            'PATCH',
            'http://localhost:18381' + reverse('api:v1:course_run-detail', kwargs={'key': course_run.key}),
            json=request_data)
        response.raise_for_status()
        return response.json()

    def get_course_key(self, organization_key, number):
        """
        Given organization key and course number, return course key.
        """
        return '{org}+{number}'.format(org=organization_key, number=number)
