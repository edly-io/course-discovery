import logging

logger = logging.getLogger(__name__)


def get_edly_sub_organization(request):
    """
    Get edly-sub-org value from edly-user-info cookie.
    request: DRF request object
    edly_sub_org: Returns edly sub organization key
    """
    edly_user_info = request.COOKIES.get('edly-user-info') or {'edly_sub_org': 'edly'}
    return edly_user_info.get('edly_sub_org')
