import os

BASE_DIR = os.path.dirname(__file__)
SITE_ID = 1

# Application definition

INSTALLED_APPS = (
    'interface',
    'interface.apps.controlpanel',
    'django.contrib.admin',
    'django.contrib.sites.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
)
MEDIA_ROOT = BASE_DIR+'media/'
MEDIA_ROOT_ADMIN = BASE_DIR+'media-admin/'
MEDIA_URL = '/media/'
ROOT_URLCONF = 'interface.urls'
WSGI_APPLICATION = 'interface.wsgi.application'

# Hack that ensures all incoming requests are seen as HTTPS

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO',None)

# Enable access to session cookies to Javascript

SESSION_COOKIE_HTTPONLY = False

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

