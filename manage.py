#!/usr/bin/env python

import os, sys, subprocess

# Remingd and django non-rel developers not to user `runserver`
if 'runserver' in sys.argv:
    sys.stderr.write(
        "Error: please uses `dev_appserver.py` to run your development server\n")
    sys.exit(1)

# Add appengine's paths (path list taken from dev_appserver.py)
# todo, don't use `which` here, find a cross-platform way
process = subprocess.Popen('readlink `which dev_appserver.py`', shell=True, stdout=subprocess.PIPE)
path = os.path.abspath(os.path.dirname(os.path.realpath(process.stdout.read())))

extra_paths = [
  path,
  # make sure django is first in case there are other django's on the system
  os.path.join(path, 'lib', 'django_1_1'),
  os.path.join(path, 'lib', 'antlr3'),
  os.path.join(path, 'lib', 'fancy_urllib'),
  os.path.join(path, 'lib', 'ipaddr'),
  os.path.join(path, 'lib', 'protorpc'),
  os.path.join(path, 'lib', 'webob'),
  os.path.join(path, 'lib', 'webapp2'),
  os.path.join(path, 'lib', 'yaml', 'lib'),
  os.path.join(path, 'lib', 'simplejson'),
  os.path.join(path, 'lib', 'google.appengine._internal.graphy'),
]

sys.path = extra_paths + sys.path

from django.core.management import execute_manager

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write(
        "Error: Can't find the file `settings.py` in the directory"
        "containing %r. It appears you've customized things.\nYou'll have"
        "to run django-admin.py, passing it your settings module.\n(If the"
        "file `settings.py` does indeed exist, it's causing an ImportError"
        "somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__": execute_manager(settings)
