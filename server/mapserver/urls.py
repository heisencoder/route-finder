from django.conf import settings
from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()



urlpatterns = patterns('',
    #url(r'^admin/', include(admin.site.urls)),
    #url(r'^map/', include('website.urls')),
    url(r'^lpsolver/', include('lpsolver.urls')),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_DOC_ROOT}),
    url(r'^', include('website.urls')),
)
