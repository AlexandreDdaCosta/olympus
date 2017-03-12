from django.conf.urls import url

from interface.apps.blog.views import FrontPage

urlpatterns = [
    url(r'', FrontPage.as_view(), name='blog_frontpage'),
]
