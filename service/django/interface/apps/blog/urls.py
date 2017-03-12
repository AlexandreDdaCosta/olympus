from django.conf.urls import patterns, url

from interface.apps.blog.views import FrontPage

urlpatterns = patterns[
    url(r'', FrontPage.as_view(),  name='blog_frontpage'),
]
