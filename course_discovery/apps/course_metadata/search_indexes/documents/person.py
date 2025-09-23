from django.conf import settings
from django_elasticsearch_dsl import Index, fields

from course_discovery.apps.course_metadata.models import Person, Position

from .analyzers import edge_ngram_completion, case_insensitive_keyword
from .common import BaseDocument

__all__ = ('PersonDocument',)

PERSON_INDEX_NAME = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
PERSON_INDEX = Index(PERSON_INDEX_NAME)
PERSON_INDEX.settings(number_of_shards=1, number_of_replicas=1, blocks={'read_only_allow_delete': None})


@PERSON_INDEX.doc_type
class PersonDocument(BaseDocument):
    """
    Person Elasticsearch document.
    """

    bio = fields.TextField()
    bio_language = fields.TextField()
    full_name = fields.TextField(
        fields={
            'edge_ngram_completion': fields.TextField(analyzer=edge_ngram_completion),
            'lower': fields.TextField(analyzer=case_insensitive_keyword)
        }
    )
    get_profile_image_url = fields.TextField()
    organizations = fields.KeywordField(multi=True)
    position = fields.TextField(multi=True)
    salutation = fields.TextField()
    full_name_override = fields.KeywordField()
    marketing_id = fields.IntegerField()
    marketing_url = fields.TextField()
    designation = fields.TextField()
    created = fields.DateField()
    given_name = fields.TextField()
    family_name = fields.TextField()
    slug = fields.TextField()
    email = fields.TextField()
    major_works = fields.TextField()
    published = fields.BooleanField()
    phone_number = fields.TextField()
    website = fields.TextField()
    social_networks = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'type': fields.KeywordField(),
        'title': fields.TextField(),
        'display_title': fields.TextField(),
        'url': fields.TextField(),
    })
    areas_of_expertise = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'value': fields.TextField(),
    })

    def prepare_aggregation_key(self, obj):
        return 'person:{}'.format(obj.uuid)

    def prepare_aggregation_uuid(self, obj):
        return 'person:{}'.format(obj.uuid)

    def prepare_bio_language(self, obj):
        if obj.bio_language:
            return obj.bio_language.name
        return None

    def prepare_organizations(self, obj):
        course_runs = obj.courses_staffed.all()
        all_organizations = [course_run.course.authoring_organizations.all() for course_run in course_runs]
        formatted_organizations = [org.key for orgs in all_organizations for org in orgs]
        return formatted_organizations

    def prepare_position(self, obj):
        try:
            position = Position.objects.get(person=obj)
        except Position.DoesNotExist:
            return []
        return [position.title, position.organization_override]
    
    def prepare_full_name_override(self, obj):
        return getattr(obj, 'full_name', None)
    
    def prepare_marketing_id(self, obj):
        return getattr(obj, 'marketing_id', None)
    
    def prepare_marketing_url(self, obj):
        return getattr(obj, 'marketing_url', None)
    
    def prepare_designation(self, obj):
        return getattr(obj, 'designation', None)
    
    def prepare_family_name(self, obj):
        return getattr(obj, 'family_name', None)
    
    def prepare_email(self, obj):
        return getattr(obj, 'email', None)
    
    def prepare_major_works(self, obj):
        return getattr(obj, 'major_works', None)
    
    def prepare_phone_number(self, obj):
        return getattr(obj, 'phone_number', None)
    
    def prepare_website(self, obj):
        return getattr(obj, 'website', None)
        
    def prepare_social_networks(self, obj):
        networks = obj.person_networks.all()
        return [{
            'id': network.id,
            'type': network.type,
            'title': network.title,
            'display_title': network.display_title,
            'url': network.url,
        } for network in sorted(networks, key=lambda x: x.id)]
    
    def prepare_areas_of_expertise(self, obj):
        areas = obj.areas_of_expertise.all()
        return [{
            'id': area.id,
            'value': area.value,
        } for area in sorted(areas, key=lambda x: x.id)]

    def prepare_get_profile_image_url(self, obj):
        return obj.profile_image_url

    def get_queryset(self, excluded_restriction_types=None):  # pylint: disable=unused-argument
        return super().get_queryset().select_related('bio_language').prefetch_related('areas_of_expertise', 'person_networks')

    class Django:
        """
        Django Elasticsearch DSL ORM Meta.
        """

        model = Person
        queryset_pagination = settings.ELASTICSEARCH_DSL_QUERYSET_PAGINATION

    class Meta:
        """
        Meta options.
        """

        parallel_indexing = True
