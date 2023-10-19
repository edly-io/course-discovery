"""
Views for Dataloader API.
"""
import logging

from discovery_dataloader_app import serializers
from django_elasticsearch_dsl_drf.constants import (
    LOOKUP_FILTER_TERM, LOOKUP_FILTER_TERMS, LOOKUP_QUERY_EXCLUDE,
)
from django_elasticsearch_dsl_drf.filter_backends import DefaultOrderingFilterBackend, FilteringFilterBackend, MultiMatchSearchFilterBackend, SearchFilterBackend
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from course_discovery.apps.api.v1.views.course_runs import CourseRunViewSet
from course_discovery.apps.api.v1.views.search import CourseRunSearchViewSet
from course_discovery.apps.core.models import Partner
from course_discovery.apps.discovery_dataloader_app.tasks import run_dataloader

logger = logging.getLogger(__name__)


class DiscoveryDataLoaderView(APIView):
    """
    Refresh course metadata from external sources.
    """
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        """
        Loads and updates course runs from the given service.
        """
        raw_data = request.data.copy()
        partner = raw_data.get('partner')
        course_id = raw_data.get('course_id')
        service = raw_data.get('service')
        if not any([partner, course_id, service]):
            return Response(
                {'error': 'Missing information'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            partner = Partner.objects.get(short_code=partner)
        except Partner.DoesNotExist:
            return Response(
                {'error': 'Partner does not exist'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            CourseKey.from_string(course_id)
        except Exception:
            return Response(
                {'error': 'Course id is not valid.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if service not in ['lms', 'ecommerce', 'wordpress']:
            return Response(
                {
                    'error': 'Data Loader for service: {} is not handled by API'.format(
                        service
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        run_dataloader.delay(partner.short_code, course_id, service)

        return Response(
            {'message': "Course Sync'd with {}".format(service)},
            status=status.HTTP_200_OK,
        )


class DataLoaderCourseRunSearchViewSet(CourseRunSearchViewSet):
    detail_serializer_class = serializers.DataLoaderCourseRunSearchModelSerializer
    serializer_class = serializers.DataLoaderCourseRunSearchDocumentSerializer

    filter_backends = [
        FilteringFilterBackend,
        SearchFilterBackend,
        MultiMatchSearchFilterBackend,
        DefaultOrderingFilterBackend,
    ]

    search_fields = (
        'title',
        'short_description',
        'full_description'
    )

    filter_fields = {
        'key': {'field': 'key.raw', 'lookups': [LOOKUP_FILTER_TERM, LOOKUP_FILTER_TERMS, LOOKUP_QUERY_EXCLUDE]},
        'published': 'published',
        'availability': 'availability',
        'featured': 'course_overridden',
        'title': 'title',
        'number': 'number',
    }
