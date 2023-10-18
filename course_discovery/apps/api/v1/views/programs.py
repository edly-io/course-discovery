import base64

from django.core.files.base import ContentFile
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as rest_framework_filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from course_discovery.apps.api import filters, serializers
from course_discovery.apps.api.cache import CompressedCacheResponseMixin
from course_discovery.apps.api.pagination import ProxiedPagination
from course_discovery.apps.api.utils import get_query_param
from course_discovery.apps.course_metadata.models import Course, CourseRun, Organization, Program


class ProgramViewSet(CompressedCacheResponseMixin, viewsets.ModelViewSet):
    """ Program resource. """
    lookup_field = 'uuid'
    lookup_value_regex = '[0-9a-f-]+'
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, rest_framework_filters.OrderingFilter)
    filterset_class = filters.ProgramFilter

    # Explicitly support PageNumberPagination and LimitOffsetPagination. Future
    # versions of this API should only support the system default, PageNumberPagination.
    pagination_class = ProxiedPagination

    def get_serializer_class(self):
        if self.action == 'list':
            if self.request.query_params.get('extended'):
                return serializers.MinimalExtendedProgramSerializer
            return serializers.MinimalProgramSerializer
        return serializers.ProgramSerializer

    def get_queryset(self):
        # This method prevents prefetches on the program queryset from "stacking,"
        # which happens when the queryset is stored in a class property.
        partner = self.request.site.partner
        q = self.request.query_params.get('q')
        program_uuid = self.request.parser_context.get('kwargs').get('uuid')
        queryset = Program.objects.filter(partner=partner).order_by('id')
        if program_uuid:
            queryset = Program.objects.filter(uuid=program_uuid)
        elif q:
            queryset = Program.search(q, queryset=queryset)
        return self.get_serializer_class().prefetch_queryset(queryset=queryset, partner=partner)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        query_params = ['exclude_utm', 'use_full_course_serializer', 'published_course_runs_only',
                        'marketable_enrollable_course_runs_with_archived']
        for query_param in query_params:
            context[query_param] = get_query_param(self.request, query_param)

        return context

    def prepare_and_set_read_only_data(self, data, context):
        """
        Extracts read only data from data dictionary and sets it in context.
        """
        authoring_organizations = data.pop('authoring_organizations', None)
        if authoring_organizations is not None:
            context['authoring_organizations'] = Organization.objects.filter(key__in=authoring_organizations).distinct()

        credit_backing_organizations = data.pop('credit_backing_organizations', None)
        if credit_backing_organizations is not None:
            context['credit_backing_organizations'] = Organization.objects.filter(key__in=credit_backing_organizations).distinct()

        course_run_keys = data.pop('course_runs', None)
        if course_run_keys is not None:
            course_runs = CourseRun.objects.filter(key__in=course_run_keys).distinct()
            courses = Course.objects.filter(key__in=course_runs.values('course__key').distinct())
            excluded_course_runs = CourseRun.objects.filter(course__in=courses).exclude(key__in=course_run_keys).distinct()

            context['courses'] = courses
            context['excluded_course_runs'] = excluded_course_runs
          
        context['one_click_purchase_enabled'] = data.get('featured', False)   # mapped featured field to one_click_purchase_enableds

    def create(self, request, *args, **kwargs):
        """
        Create a new program.
        """
        data = request.data
        context = {}

        self.prepare_and_set_read_only_data(data, context)

        context['partner'] = request.site.partner
        context['request'] = request

        serializer = serializers.ProgramSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Update exsisting program.
        """
        data = request.data
        context = {}
        instance = Program.objects.get(uuid=kwargs.get('uuid'))

        self.prepare_and_set_read_only_data(data, context)

        context['request'] = request

        serializer = serializers.ProgramSerializer(instance, data=data, context=context)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def list(self, request, *args, **kwargs):
        """ List all programs.
        ---
        parameters:
            - name: marketable
              description: Retrieve marketable programs. A program is considered marketable if it is active
                and has a marketing slug.
              required: false
              type: integer
              paramType: query
              multiple: false
            - name: published_course_runs_only
              description: Filter course runs by published ones only
              required: false
              type: integer
              paramType: query
              mulitple: false
            - name: marketable_enrollable_course_runs_with_archived
              description: Restrict returned course runs to those that are published, have seats,
                and can be enrolled in now. Includes archived courses.
              required: false
              type: integer
              paramType: query
              mulitple: false
            - name: exclude_utm
              description: Exclude UTM parameters from marketing URLs.
              required: false
              type: integer
              paramType: query
              multiple: false
            - name: use_full_course_serializer
              description: Return all serialized course information instead of a minimal amount of information.
              required: false
              type: integer
              paramType: query
              multiple: false
            - name: types
              description: Filter by comma-separated list of program type slugs
              required: false
              type: string
              paramType: query
              multiple: false
            - name: q
              description: Elasticsearch querystring query. This filter takes precedence over other filters
              required: false
              type: string
              paramType: query
              multiple: false
            - name: extended
              description: Boolean flag to include additional fields in the list response payload
        """
        if get_query_param(self.request, 'uuids_only'):
            # DRF serializers don't have good support for simple, flat
            # representations like the one we want here.
            queryset = self.filter_queryset(Program.objects.filter(partner=self.request.site.partner))
            uuids = queryset.values_list('uuid', flat=True)

            return Response(uuids)

        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def update_card_image(self, request, *_args, **_kwargs):
        if not self.request.user.is_staff:
            raise PermissionDenied
        program = self.get_object()
        image_data = request.data.get('image', None)
        if image_data and isinstance(image_data, str) and image_data.startswith('data:image'):
            # base64 encoded image - decode
            file_format, imgstr = image_data.split(';base64,')  # format ~= data:image/X;base64,/xxxyyyzzz/
            ext = file_format.split('/')[-1]  # guess file extension
            image_data = ContentFile(base64.b64decode(imgstr), name=f'tmp.{ext}')
            program.card_image.save(image_data.name, image_data)
            msg = 'Successfully updated program card image for program {uuid}: {title}'.format(uuid=program.uuid,
                                                                                               title=program.title)
            return Response(msg)
        else:
            return Response('Bad image data in request', status=status.HTTP_400_BAD_REQUEST)
