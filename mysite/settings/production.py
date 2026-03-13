from .base import *

DEBUG = False

ALLOWED_HOSTS = ["private.marianstreet.tokyo"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = ["https://private.marianstreet.tokyo"]
