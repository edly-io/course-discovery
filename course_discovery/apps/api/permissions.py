import logging
from rest_framework.permissions import BasePermission

log = logging.getLogger(__name__)


class ReadOnlyByPublisherUser(BasePermission):
    """
    Custom Permission class to check user is a publisher user.
    """
    def has_permission(self, request, view):
        log.info(request.user)
        log.info(request.user.groups)
        if request.method == 'GET':
                return request.user.groups.exists()
        return True
