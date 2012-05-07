from django.conf.urls.defaults import *
from core import views

urlpatterns = patterns(
    '',
    url(r'^$', views.JSTest.as_view(), {}, name='js-test'),
)
