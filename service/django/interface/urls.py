from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/welcome/')),
    url(r'^admin/', admin.site.urls),
    url(r'^blog/', include('interface.apps.blog.urls')),
    url(r'^login/', auth_views.LoginView.as_view()),
    url(r'^logout/', auth_views.LogoutView.as_view()),
    url(r'^photography/', include('interface.apps.photography.urls')),
    url(r'^welcome/', include('interface.apps.welcome.urls')),
]
