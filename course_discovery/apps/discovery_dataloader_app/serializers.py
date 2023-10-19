from rest_framework import serializers

from course_discovery.apps.api.serializers import ContentTypeSerializer, CourseRunWithProgramsSerializer
from course_discovery.apps.course_metadata.models import CourseRun
from course_discovery.apps.course_metadata.search_indexes.documents import CourseRunDocument
from course_discovery.apps.course_metadata.search_indexes.serializers.common import DocumentDSLSerializerMixin
from course_discovery.apps.course_metadata.search_indexes.serializers.course_run import (
    CourseRunSearchDocumentSerializer
)


class DataLoaderCourseRunWithProgramsSerializer(CourseRunWithProgramsSerializer):
    featured = serializers.ReadOnlyField(source='course_overridden')

    class Meta(CourseRunWithProgramsSerializer.Meta):
        fields = CourseRunWithProgramsSerializer.Meta.fields + ('featured', )
        read_only_fields = ('card_image_url',)


class DataLoaderCourseRunSearchDocumentSerializer(CourseRunSearchDocumentSerializer):

    featured = serializers.ReadOnlyField(source='course_overridden')

    class Meta(CourseRunSearchDocumentSerializer.Meta):
        """ Meta options. """

        document = CourseRunDocument
        fields = CourseRunSearchDocumentSerializer.Meta.fields + ('card_image_url', 'featured', 'outcome', )


class DataLoaderCourseRunSearchModelSerializer(
    DocumentDSLSerializerMixin, ContentTypeSerializer, DataLoaderCourseRunWithProgramsSerializer
):
    class Meta(DataLoaderCourseRunWithProgramsSerializer.Meta):
        document = CourseRunDocument
        fields = ContentTypeSerializer.Meta.fields + DataLoaderCourseRunWithProgramsSerializer.Meta.fields
