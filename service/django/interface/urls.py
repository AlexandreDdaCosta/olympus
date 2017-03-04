from django.conf.urls import patterns, url

import interface.apps.controlpanel

from django.contrib import admin
from django.contrib.sites.models import Site

admin.autodiscover()

urlpatterns = patterns('',
  url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
  url(r'^accounts/logout/$', 'django.contrib.auth.views.logout'), 
  url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'admin/login.html'}, name='login'),
  url(r'^logout/$', 'django.contrib.auth.views.logout', name='logout'),
)
