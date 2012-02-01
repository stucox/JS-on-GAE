djappengine 
===========

A streamlined django setup for appengine.

Rather than using `django non-rel`_, this approach uses the `django 1.2
third-party library`_ available for the 2.7 runtime. You might prefer it if
you'd like to use `appEngine's Model class`_ for your models.

The philosophy is to use appengine's and django's strengths, and to keep
configuration and baggage to a minimum.

What's in the box?
------------------

This is work in progress, but here's where we'd like to get to.

- A bare-bones app.yaml configuration
- A WSGI app that connects djago to AppEngine, and helps route logging
- Django settings
- A caching backend, as AppEngine's memcache is not quite what django espects
- A session engine, which uses the caching backend, and writes through to the
  datastore

.. _`django non-rel`: http://www.allbuttonspressed.com/projects/django-nonrel

.. _`django 1.2 third-party library`: http://
   code.google.com/appengine/docs/python/tools/libraries27.html

.. _`appEngine's Model class`: http://
   code.google.com/appengine/docs/python/datastore/modelclass.html
