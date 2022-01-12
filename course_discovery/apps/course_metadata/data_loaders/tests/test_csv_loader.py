"""
Unit tests for CSV Data loader.
"""
from tempfile import NamedTemporaryFile
from unittest import mock

import responses
import six
from testfixtures import LogCapture

from course_discovery.apps.api.v1.tests.test_views.mixins import APITestCase, OAuth2Mixin
from course_discovery.apps.core.tests.factories import USER_PASSWORD, UserFactory
from course_discovery.apps.course_metadata.data_loaders.csv_loader import CSVDataLoader
from course_discovery.apps.course_metadata.data_loaders.tests import mock_data
from course_discovery.apps.course_metadata.models import Course, CourseRun
from course_discovery.apps.course_metadata.tests.factories import OrganizationFactory

LOGGER_PATH = 'course_discovery.apps.course_metadata.data_loaders.csv_loader'


@mock.patch(
    'course_discovery.apps.course_metadata.data_loaders.configured_jwt_decode_handler',
    return_value={'preferred_username': 'test_username'}
)
class TestCSVDataLoader(OAuth2Mixin, APITestCase):
    """
    Test Suite for CSVDataLoader.
    """
    # The list to define order of the header keys in csv. The order here is important to keep header->values in sync.
    CSV_DATA_KEYS_ORDER = [
        'organization', 'title', 'number', 'course_enrollment_track', 'image', 'short_description',
        'long_description', 'what_will_you_learn', 'course_level', 'primary_subject', 'verified_price', 'collaborators',
        'syllabus', 'prerequisites', 'learner_testimonials', 'frequently_asked_questions', 'additional_information',
        'about_video_link', 'secondary_subject', 'tertiary_subject', 'ofac_restriction', 'publish_date',
        'start_date', 'start_time', 'end_date', 'end_time', 'course_run_enrollment_track', 'course_pacing', 'staff',
        'minimum_effort', 'maximum_effort', 'length', 'content_language', 'transcript_language',
        'expected_program_type', 'expected_program_name', 'upgrade_deadline_override_date',
        'upgrade_deadline_override_time'
    ]

    def setUp(self) -> None:
        super().setUp()
        self.mock_access_token()
        self.user = UserFactory.create(username="test_user", password=USER_PASSWORD, is_staff=True)
        self.client.login(username=self.user.username, password=USER_PASSWORD)

    def _write_csv(self, csv, lines_dict_list):
        """
        Helper method to write given list of data dictionaries to csv, including the csv header.
        """
        header = ''
        lines = ''
        for key in self.CSV_DATA_KEYS_ORDER:
            title_case_key = key.replace('_', ' ').title()
            header = '{}{},'.format(header, title_case_key)
        header = f"{header[:-1]}\n"

        for line_dict in lines_dict_list:
            for key in self.CSV_DATA_KEYS_ORDER:
                lines = '{}"{}",'.format(lines, line_dict[key])
            lines = f"{lines[:-1]}\n"

        csv.write(six.b(header))
        csv.write(six.b(lines))
        csv.seek(0)
        return csv

    def _setup_organization(self):
        """
        setup test-only organization.
        """
        OrganizationFactory(name='edx', key='edx', partner=self.partner)

    def mock_ecommerce_publication(self):
        """
        Mock ecommerce api calls.
        """
        url = f'{self.partner.ecommerce_api_url}publication/'
        responses.add(responses.POST, url, json={}, status=200)

    def mock_studio_push(self):
        """
        Mock the studio api calls.
        """
        studio_url = '{root}/api/v1/course_runs/'.format(root=self.partner.studio_url.strip('/'))
        responses.add(responses.POST, studio_url, status=200)
        key = 'course-v1:edx+csv_123+1T2001'
        responses.add(responses.POST, f'{studio_url}{key}/images/', status=200)

    def _assert_default_logs(self, log_capture):
        """
        Assert the initiation and completion logs are present in the logger.
        """
        log_capture.check_present(
            (
                LOGGER_PATH,
                'INFO',
                'Initiating CSV data loader flow.'
            ),
            (
                LOGGER_PATH,
                'INFO',
                'CSV loader ingest pipeline has completed.'
            )

        )

    def test_missing_organization(self, jwt_decode_patch):  # pylint: disable=unused-argument
        """
        Verify that no course and course run are created for a missing organization in the database.
        """
        with NamedTemporaryFile() as csv:
            csv = self._write_csv(csv, [mock_data.INVALID_ORGANIZATION_DATA])
            with LogCapture(LOGGER_PATH) as log_capture:
                loader = CSVDataLoader(self.partner, csv_path=csv.name)
                loader.ingest()
                self._assert_default_logs(log_capture)
                log_capture.check_present(
                    (
                        LOGGER_PATH,
                        'ERROR',
                        'Organization invalid-organization does not exist in database. Skipping CSV '
                        'loader for course CSV Course'
                    )
                )
                assert Course.objects.count() == 0
                assert CourseRun.objects.count() == 0

    def test_invalid_course_type(self, jwt_decode_patch):  # pylint: disable=unused-argument
        """
        Verify that no course and course run are created for an invalid course track type.
        """
        self._setup_organization()
        with NamedTemporaryFile() as csv:
            csv = self._write_csv(csv, [mock_data.INVALID_COURSE_TYPE_DATA])
            with LogCapture(LOGGER_PATH) as log_capture:
                loader = CSVDataLoader(self.partner, csv_path=csv.name)
                loader.ingest()
                self._assert_default_logs(log_capture)
                log_capture.check_present(
                    (
                        LOGGER_PATH,
                        'ERROR',
                        'CourseType invalid track does not exist in the database.'
                    )
                )
                assert Course.objects.count() == 0
                assert CourseRun.objects.count() == 0

    def test_invalid_course_run_type(self, jwt_decode_patch):  # pylint: disable=unused-argument
        """
        Verify that no course and course run are created for an invalid course run track type.
        """
        self._setup_organization()
        with NamedTemporaryFile() as csv:
            csv = self._write_csv(csv, [mock_data.INVALID_COURSE_RUN_TYPE_DATA])
            with LogCapture(LOGGER_PATH) as log_capture:
                loader = CSVDataLoader(self.partner, csv_path=csv.name)
                loader.ingest()
                self._assert_default_logs(log_capture)
                log_capture.check_present(
                    (
                        LOGGER_PATH,
                        'ERROR',
                        'CourseRunType invalid track does not exist in the database.'
                    )
                )
                assert Course.objects.count() == 0
                assert CourseRun.objects.count() == 0

    @responses.activate
    def test_single_valid_row_no_image(self, jwt_decode_patch):  # pylint: disable=unused-argument
        """
        Verify that no course and course run are created for an invalid course run track type.
        """
        self._setup_organization()
        self.mock_studio_push()
        self.mock_ecommerce_publication()
        with NamedTemporaryFile() as csv:
            csv = self._write_csv(csv, [mock_data.VALID_COURSE_AND_COURSE_RUN_CSV_DICT])
            with LogCapture(LOGGER_PATH) as log_capture:
                loader = CSVDataLoader(self.partner, csv_path=csv.name)
                original_client = loader.api_client
                loader.api_client = self.client
                loader.ingest()
                loader.api_client = original_client

                self._assert_default_logs(log_capture)
                log_capture.check_present(
                    (
                        LOGGER_PATH,
                        'INFO',
                        'Course key edx+csv_123 could not be found in database, creating the course.'
                    )
                )
                assert Course.objects.count() == 1
                assert CourseRun.objects.count() == 1
