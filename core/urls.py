from django.conf.urls.defaults import *
from core import views

urlpatterns = patterns(
    '',
    url(r'^$', views.HelloWorld.as_view(), {}, name='hello-world'),
)
