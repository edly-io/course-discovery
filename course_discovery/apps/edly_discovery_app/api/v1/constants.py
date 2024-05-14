"""
Constants for Edly Sites API.
"""
from enum import Enum

from django.utils.translation import ugettext as _

ERROR_MESSAGES = {
    'CLIENT_SITES_SETUP_SUCCESS': _('Client sites setup successful.'),
    'CLIENT_SITES_SETUP_FAILURE': _('Client sites setup failed.'),
}

CLIENT_SITE_SETUP_FIELDS = [
    'lms_site',
    'cms_site',
    'discovery_site',
    'payments_site',
    'wordpress_site',
    'partner_name',
    'partner_short_code',
]

DEFAULT_COURSE_ID = 'course-v1:{}+get_started_with+Edly'

class CoursePlans(Enum):
    TRIAL = 'trial'
    ESSENTIALS = 'essentials'
    ELITE_PLAN = 'elite'
    TRIAL_EXPIRED = 'trial expired'
    DEACTIVATED = 'deactivated'
    LEGACY = 'legacy'
