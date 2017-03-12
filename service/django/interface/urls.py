from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/welcome/')),
    url(r'^admin/', admin.site.urls),
    url(r'^blog/', include('interface.apps.blog.urls'), name='blog'),
    url(r'^welcome/', include('interface.apps.welcome.urls'), name='welcome'),
]
