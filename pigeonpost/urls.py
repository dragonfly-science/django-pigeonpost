try:
    from django.conf.urls import patterns, url, include
except ImportError:
    # django 1.3, etc
    from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    url(r'^admin/', include(admin.site.urls))
)
