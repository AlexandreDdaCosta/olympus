from django.urls import include, path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path(r'^$', RedirectView.as_view(url='/welcome/')),
    path(r'^admin/', admin.site.urls),
    path(r'^blog/', include('interface.apps.blog.urls')),
    path(r'^coding/', include('interface.apps.coding.urls')),
    path(r'^login/', auth_views.LoginView.as_view()),
    path(r'^logout/', auth_views.LogoutView.as_view()),
    path(r'^photography/', include('interface.apps.photography.urls')),
    path(r'^welcome/', include('interface.apps.welcome.urls')),
]
