"""
Context processors for the grants project.
These make variables available to all templates.
"""
from django.conf import settings
from decouple import config


def analytics_context(request):
    """Add Google Analytics ID to template context"""
    return {
        'GOOGLE_ANALYTICS_ID': config('GOOGLE_ANALYTICS_ID', default=''),
    }


def site_settings(request):
    """Add common site settings to template context"""
    return {
        'DEBUG': settings.DEBUG,
        'SITE_NAME': 'Canadian Grants Tracker',
    }
