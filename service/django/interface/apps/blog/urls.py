from django.urls import path

from interface.apps.blog.views import TheZodiacalLight

urlpatterns = [
    path(r'', TheZodiacalLight.as_view(), name='blog_thezodiacallight'),
]
