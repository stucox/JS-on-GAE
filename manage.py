#!/usr/bin/env python

import os, sys, subprocess

# Remingd and django non-rel developers not to user `runserver`
if 'runserver' in sys.argv: 
    sys.stderr.write( 
        "Error: please uses `dev_appserver.py` to run your development server\n") 
    sys.exit(1)

# Add appengine's django1.2 to top of the path
process = subprocess.Popen('readlink `which dev_appserver.py`', shell=True, stdout=subprocess.PIPE)
path = os.path.abspath(os.path.dirname(os.path.realpath(process.stdout.read())))
django_1_2 = os.path.join(path, 'lib', 'django_1_2')
sys.stdout.write('Inserter into path:\n%s\n' % django_1_2)
sys.path.insert(0, django_1_2)

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
