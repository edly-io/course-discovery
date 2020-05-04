import logging

logger = logging.getLogger(__name__)


def get_edly_sub_organization(request):
    """
    Get edly-sub-org value from edly-user-info cookie.
    request: DRF request object
    edly_sub_org: Returns edly sub organization key
    """
    edly_sub_org = request.COOKIES.get('logged_in_status')
    return edly_sub_org or 'edly'
