from django.conf import settings
from django_elasticsearch_dsl import Index, fields
from opaque_keys.edx.keys import CourseKey
from taxonomy.choices import ProductTypes
from taxonomy.utils import get_whitelisted_serialized_skills

from course_discovery.apps.api.utils import get_retired_run_type_ids
from course_discovery.apps.course_metadata.choices import CourseRunStatus
from course_discovery.apps.course_metadata.models import CourseRun
from course_discovery.apps.course_metadata.utils import get_product_skill_names

from .analyzers import case_insensitive_keyword, html_strip
from .common import BaseCourseDocument, filter_visible_runs

__all__ = ('CourseRunDocument',)

COURSE_RUN_INDEX_NAME = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
COURSE_RUN_INDEX = Index(COURSE_RUN_INDEX_NAME)
COURSE_RUN_INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1,
    blocks={'read_only_allow_delete': None},
)


@COURSE_RUN_INDEX.doc_type
class CourseRunDocument(BaseCourseDocument):
    """
    Course run Elasticsearch document.
    """

    announcement = fields.DateField()
    availability = fields.TextField(
        fields={'raw': fields.KeywordField(), 'lower': fields.TextField(analyzer=case_insensitive_keyword)}
    )
    authoring_organization_uuids = fields.KeywordField(multi=True)
    course_key = fields.KeywordField()
    end = fields.DateField()
    enrollment_start = fields.DateField()
    enrollment_end = fields.DateField()
    fixed_price_usd = fields.FloatField()
    first_enrollable_paid_seat_sku = fields.TextField()
    go_live_date = fields.DateField()
    has_enrollable_seats = fields.BooleanField()
    is_active = fields.BooleanField()
    has_enrollable_paid_seats = fields.BooleanField()
    hidden = fields.BooleanField()
    is_enrollable = fields.BooleanField()
    is_current_and_still_upgradeable = fields.BooleanField()
    language = fields.TextField(
        analyzer=html_strip, fields={'raw': fields.KeywordField()}
    )
    license = fields.KeywordField()
    marketing_url = fields.TextField()
    min_effort = fields.IntegerField()
    max_effort = fields.IntegerField()
    mobile_available = fields.BooleanField()
    number = fields.KeywordField()
    paid_seat_enrollment_end = fields.DateField()
    pacing_type = fields.KeywordField()
    program_types = fields.KeywordField(multi=True)
    published = fields.BooleanField()
    skill_names = fields.KeywordField(multi=True)
    skills = fields.NestedField(properties={
        'name': fields.TextField(),
        'description': fields.TextField(),
    })
    status = fields.KeywordField()
    start = fields.DateField()
    restriction_type = fields.KeywordField()
    slug = fields.TextField()
    staff_uuids = fields.KeywordField(multi=True)
    type = fields.TextField(
        attr='type_legacy',
        analyzer=html_strip,
        fields={
            'raw': fields.KeywordField(attr='type_legacy'),
            'lower': fields.TextField(analyzer=case_insensitive_keyword, attr='type_legacy')
        }
    )
    transcript_languages = fields.TextField(
        analyzer=html_strip, fields={'raw': fields.KeywordField(multi=True)}, multi=True
    )
    weeks_to_complete = fields.IntegerField()
    title_override = fields.KeywordField()
    featured = fields.BooleanField()
    is_marketing_price_set = fields.BooleanField()
    marketing_price_value = fields.TextField()
    is_marketing_price_hidden = fields.BooleanField()
    card_image_url = fields.TextField()
    yt_video_url = fields.TextField()
    course_duration_override = fields.IntegerField()
    course_difficulty = fields.KeywordField()
    course_job_role = fields.KeywordField()
    course_format = fields.KeywordField()
    course_industry_certified_training = fields.KeywordField()
    course_language = fields.KeywordField()
    course_owner = fields.KeywordField()
    created = fields.DateField()

    def prepare_title_override(self, obj):
        return getattr(obj, 'title_override', None) or obj.title
    
    def prepare_featured(self, obj):
        return getattr(obj, 'featured', None)
    
    def prepare_is_marketing_price_set(self, obj):
        return getattr(obj, 'is_marketing_price_set', None)
    
    def prepare_marketing_price_value(self, obj):
        return getattr(obj, 'marketing_price_value', None)
    
    def prepare_is_marketing_price_hidden(self, obj):
        return getattr(obj, 'is_marketing_price_hidden', None)

    def prepare_card_image_url(self, obj):
        return obj.card_image_url

    def prepare_yt_video_url(self, obj):
        return getattr(obj, 'yt_video_url', None)
    
    def prepare_course_duration_override(self, obj):
        return getattr(obj, 'course_duration_override', None)
    
    def prepare_course_difficulty(self, obj):
        return getattr(obj, 'course_difficulty', None)
    
    def prepare_course_job_role(self, obj):
        return getattr(obj, 'course_job_role', None)
    
    def prepare_course_format(self, obj):
        return getattr(obj, 'course_format', None)
    
    def prepare_course_language(self, obj):
        return getattr(obj, 'course_language', None)
    
    def prepare_course_owner(self, obj):
        return getattr(obj, 'course_owner', None)
    
    def prepare_course_industry_certified_training(self, obj):
        return getattr(obj, 'course_industry_certified_training', None)

    def prepare_created(self, obj):
        return getattr(obj, 'created', None)
    
    def prepare_aggregation_key(self, obj):
        # Aggregate CourseRuns by Course key since that is how we plan to dedup CourseRuns on the marketing site.
        return 'courserun:{}'.format(obj.course.key)

    def prepare_aggregation_uuid(self, obj):
        return 'courserun:{}'.format(obj.uuid)

    def prepare_course_key(self, obj):
        return obj.course.key

    def prepare_first_enrollable_paid_seat_sku(self, obj):
        return obj.first_enrollable_paid_seat_sku()

    def prepare_is_active(self, obj):
        return self._prepare_is_active(obj)

    def prepare_is_current_and_still_upgradeable(self, obj):
        return obj.is_current_and_still_upgradeable()

    def prepare_has_enrollable_paid_seats(self, obj):
        return obj.has_enrollable_paid_seats()

    def prepare_language(self, obj):
        return self._prepare_language(obj.language)

    def prepare_number(self, obj):
        course_run_key = CourseKey.from_string(obj.key)
        return course_run_key.course

    def prepare_org(self, obj):
        course_run_key = CourseKey.from_string(obj.key)
        return course_run_key.org

    def prepare_paid_seat_enrollment_end(self, obj):
        return obj.get_paid_seat_enrollment_end()

    def prepare_partner(self, obj):
        return obj.course.partner.short_code

    def prepare_published(self, obj):
        return obj.status == CourseRunStatus.Published

    def prepare_seat_types(self, obj):
        return [seat_type.slug for seat_type in obj.seat_types]

    def prepare_skill_names(self, obj):
        return get_product_skill_names(obj.course.key, ProductTypes.Course)

    def prepare_restriction_type(self, obj):
        if hasattr(obj, "restricted_run"):
            return obj.restricted_run.restriction_type
        return None

    def prepare_skills(self, obj):
        return get_whitelisted_serialized_skills(obj.course.key, product_type=ProductTypes.Course)

    def prepare_staff_uuids(self, obj):
        return [str(staff.uuid) for staff in obj.staff.all()]

    def prepare_transcript_languages(self, obj):
        return [
            self._prepare_language(language)
            for language in obj.transcript_languages.all()
        ]

    def get_queryset(self, excluded_restriction_types=None):  # pylint: disable=unused-argument
        retired_type_ids = get_retired_run_type_ids()
        return filter_visible_runs(
            super().get_queryset()
                   .exclude(type_id__in=retired_type_ids)
                   .select_related('course')
                   .select_related('course__type')
                   .prefetch_related('seats__type')
                   .prefetch_related('transcript_languages')
        )

    class Django:
        """
        Django Elasticsearch DSL ORM Meta.
        """

        model = CourseRun
        queryset_pagination = settings.ELASTICSEARCH_DSL_QUERYSET_PAGINATION

    class Meta:
        """
        Meta options.
        """

        parallel_indexing = True
