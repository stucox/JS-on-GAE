import os
import sys
import logging

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django
import django.core.signals
import django.dispatch
import django.db

sys.path.extend(['lib'])

PRODUCTION =\
    os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or\
    os.getenv('SETTINGS_MODE') == 'prod'

if not PRODUCTION:
    logging.info('Development django: %s' % django.__file__)
    logging.info(django.get_version())


# Logging configuration
# see: http://code.google.com/appengine/articles/django.html

def log_exception(*args, **kwds):
    logging.exception('Exception in request:')

# Log errors.
django.dispatch.Signal.connect(
    django.core.signals.got_request_exception, log_exception)

# Unregister the rollback event handler.
django.dispatch.Signal.disconnect(
    django.core.signals.got_request_exception,
    django.db._rollback_on_exception)

# WSGI app
import django.core.handlers.wsgi
app = django.core.handlers.wsgi.WSGIHandler()
