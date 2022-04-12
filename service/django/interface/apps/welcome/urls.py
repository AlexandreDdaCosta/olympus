from django.urls import path

from interface.apps.welcome.views import Home

urlpatterns = [
    path(r'', Home.as_view(), name='welcome_home'),
]
