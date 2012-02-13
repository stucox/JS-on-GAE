import os
import sys
import django
import logging

"""
for key, value in os.environ.iteritems():
    logging.info('%s: %s' % (key, value))
"""

sys.path.extend(['lib'])

dev = os.environ['SERVER_NAME'] == 'localhost'

os.environ['DJANGO_DEBUG'] = dev and '1' or '0'

if dev:
    logging.info('Development django: %s' % django.__file__)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
app = django.core.handlers.wsgi.WSGIHandler()


'''
    Logging configuration
        with Django 1.2 need to set up a log_exception method so
        the error appears within the Logs section on app engine admin
        
        Connect log_exception as a Signal
        see : http://code.google.com/appengine/articles/django.html

'''

def log_exception(*args, **kwds):
    logging.exception('Exception in request:')

import django.core.signals
import django.dispatch
import django.db

# Log errors.
django.dispatch.Signal.connect(
    django.core.signals.got_request_exception, log_exception)

# Unregister the rollback event handler.
django.dispatch.Signal.disconnect(
    django.core.signals.got_request_exception,
    django.db._rollback_on_exception)

