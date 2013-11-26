from django.conf.urls import patterns, url

from website import views

# / ought to redirect to /index.html

urlpatterns = patterns('',
    url(r'^(index\.html)$', views.staticFile, name='filename'),
)

