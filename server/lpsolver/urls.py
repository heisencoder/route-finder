from django.conf.urls import patterns, url

from lpsolver import views


urlpatterns = patterns('',
url(r'^solver\.request$', views.solverRequest),
#url(r'^', views.solverRequest),
)
