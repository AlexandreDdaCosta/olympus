from django.urls import url

from interface.apps.welcome.views import Home

urlpatterns = [
    url(r'', Home.as_view(), name='welcome_home'),
]
