import os

# Local configurations
from interface.settings_local import * #  noqa: F403

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_ID = 1

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'interface',
    'interface.apps.cookbook',
    'django_album_olympus',
    'django_blog_olympus',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = True
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
MEDIA_ROOT = '/srv/www/django/interface/media'
MEDIA_ROOT_ADMIN = '/srv/www/django/interface/media-admin'
MEDIA_URL = '/media/'
STATIC_URL = '/static/'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.' +
        'UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.' +
        'MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.' +
        'CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.' +
        'NumericPasswordValidator',
    },
]
ROOT_URLCONF = 'interface.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR + r'/interface/templates/',
            BASE_DIR + r'/interface/apps/welcome/templates',
            BASE_DIR + r'/interface/apps/projects/templates',
            BASE_DIR + r'/interface/apps/cookbook/templates',
            BASE_DIR + r'/interface/apps/security_analyzer/templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'interface.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Added to handle warnings about lack of explicitly defined
# primary key type, starting in Django 3.2
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Hack that ensures all incoming requests are seen as HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', None)

# Enable access to session cookies to Javascript
SESSION_COOKIE_HTTPONLY = False

# Error logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
