from django.conf.urls import patterns, url

from website import views


urlpatterns = patterns('',
    url(r'^$', views.indexFile),
    url(r'^index\.html$', views.indexFile),
)

