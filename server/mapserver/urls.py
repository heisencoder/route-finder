from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()



urlpatterns = patterns('',
    #url(r'^admin/', include(admin.site.urls)),
    #url(r'^map/', include('website.urls')),
    url(r'^lpsolver/', include('lpsolver.urls')),
    url(r'^', include('website.urls')),     
)
