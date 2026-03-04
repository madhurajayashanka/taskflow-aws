"""
Production settings for TaskFlow.
"""
import os
from .base import *  # noqa: F401,F403

DEBUG = False

# ── Fail-fast if SECRET_KEY not explicitly set ──────────────────────
SECRET_KEY = os.environ['SECRET_KEY']  # KeyError = intentional fail-fast

# ── Security ────────────────────────────────────────────────────────
# SSL redirect is handled by Nginx (HTTP→HTTPS 301). Django trusts the
# X-Forwarded-Proto header from Nginx to know the original scheme.
SECURE_SSL_REDIRECT = os.environ.get('ENABLE_SSL_REDIRECT', 'true').lower() == 'true'
SECURE_HSTS_SECONDS = 63072000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── S3 File Storage ────────────────────────────────────────────────
# On EC2, boto3 auto-discovers credentials from the IAM Instance Profile.
# No static access keys needed — this is the AWS best practice.
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME', '')
AWS_S3_REGION_NAME = os.environ.get('AWS_REGION', 'us-east-1')
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 3600

# ── DRF — JSON only in production ──────────────────────────────────
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
]
