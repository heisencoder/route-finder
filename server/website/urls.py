from django.conf.urls import patterns, url

from website import views


urlpatterns = patterns('',
    url(r'^(index\.html)$', views.staticFile, name='filename'),
    url(r'^(javascript/route-finder\.js)$', views.staticFile, name='filename'),
)

