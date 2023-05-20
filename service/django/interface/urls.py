from django.urls import include, path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path(r'', RedirectView.as_view(url='/welcome/')),
    path(r'admin/', admin.site.urls),
    path(r'album/', include('django_album_olympus.urls')),
    path(r'blog/', include('django_blog_olympus.urls')),
    path(r'cookbook/', include('interface.apps.cookbook.urls')),
    path(r'login/', auth_views.LoginView.as_view()),
    path(r'logout/', auth_views.LogoutView.as_view()),
    path(r'projects/', include('interface.apps.projects.urls')),
    path(r'securities/', include('interface.apps.security_analyzer.urls')),
    path(r'welcome/', include('interface.apps.welcome.urls')),
]
