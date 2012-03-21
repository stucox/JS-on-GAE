import os
import sys

HTTP_HOST = os.environ.get('HTTP_HOST')

PROJDIR = os.path.abspath(os.path.dirname(__file__))
APPDIR = os.path.join(PROJDIR, 'core')

# todo: duplication of that in main.py?
sys.path.extend([os.path.join(PROJDIR, 'lib')])

# Set by main.py to '1' on dev and '0' on production
DJANGO_DEBUG = os.environ.get('DJANGO_DEBUG', '1')
DEBUG = bool(int(DJANGO_DEBUG))
TEMPLATE_DEBUG = DEBUG

# Uncomment these DB definitions to use Cloud SQL.  MySQL is used locally for
# development. This is not a requirement, you can also connect to Cloud SQL in
# your development environment, whether that be the production instance or a
# development instance.
# See https://developers.google.com/cloud-sql/docs/django#development-settings
"""
# CLoud SQL with local mysql substitue for dev
if (os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or
    os.getenv('SETTINGS_MODE') == 'prod'):
    # Running on production App Engine, so use a Google Cloud SQL database.
    DATABASES = {
        'default': {
            'ENGINE': 'google.appengine.ext.django.backends.rdbms',
            'INSTANCE': 'my_project:instance1',
            'NAME': 'my_db',
        }
    }
else:
    # Running in development, so use a local MySQL database.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'USER': '',
            'PASSWORD': '',
            'HOST': 'localhost',
            'NAME': '',
        }
    }
"""

# A custom cache backend using AppEngine's memcached
CACHES = {
    'default': {
        'BACKEND': 'appenginecache.CacheClass',
        }
}

# Custom session engine using our cache or writing through to the datastore
# If using SQL, can we use django's standard write through?
SESSION_ENGINE = "appengine_sessions.backends.cached_db"

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'America/Chicago'

# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = False

USE_L10N = False

template_context_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.contrib.messages.context_processors.messages',)

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '!cjx1x7vn8ukbemz#_tr99nzethtpsn%f_n-737)$#-#goj(x-'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(APPDIR, 'templates')
)

INSTALLED_APPS = (
    'appengine_sessions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'core'
)

