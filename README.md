JS-on-GAE
=========
[DEMO ON APPSPOT](//sc-js-on-gae.appspot.com/)

This is a quick demo of Javascript code being shared between server and client, using [pyjon](//code.google.com/p/pyjon/) to evaluate Javascript in a Python environment with Django on Google App Engine.

Enter some numbers then click the relevant button to either evaluate it on the server or in your browser. The adding function is only defined once, in `shared-functions.js`, which is read and evaluated by the server, as well as being served to the browser.

Obviously this is massive overkill for adding two numbers(!), but the concept could be applied to more complex calculations, operations on objects, etc, such that common logic only needs to be defined once.
