"""
Development settings for TaskFlow.
"""
from .base import *  # noqa: F401,F403

DEBUG = True

# In development, allow all hosts for convenience
ALLOWED_HOSTS = ['*']

# CORS — allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# File storage — local filesystem in development
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Browsable API enabled in development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]

# Disable throttling in development (allows running E2E tests)
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []  # noqa: F405
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {  # noqa: F405
    'anon': None,
    'user': None,
}
