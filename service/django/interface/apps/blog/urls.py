from django.conf.urls import url

from interface.apps.blog.views import TheZodiacalLight

urlpatterns = [
    url(r'', TheZodiacalLight.as_view(), name='blog_TheZodiacalLight'),
]
