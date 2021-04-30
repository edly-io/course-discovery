"""
Permissions for Edly Sites API.
"""
import logging

from django.conf import settings
from rest_framework import permissions

logger = logging.getLogger(__name__)


class CanAccessCurrentSite(permissions.BasePermission):
    """
    Permission to check if the current site is allowed for the user.
    """

    def has_permission(self, request, view):
        """
        Checks for user's permission for current site.
        """
        return request.user.is_staff or request.user.username == settings.EDLY_PANEL_WORKER_USER
