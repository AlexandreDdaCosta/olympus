from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^/', include('interface.apps.welcome.urls'), name='welcome'),
    url(r'^admin/', admin.site.urls),
    url(r'^blog/', include('interface.apps.blog.urls'), name='blog'),
]
