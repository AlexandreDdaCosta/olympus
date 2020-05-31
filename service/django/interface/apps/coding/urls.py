from django.conf.urls import url

from interface.apps.photography.views import SpaceshipEarth

urlpatterns = [
    url(r'', TheKuiperBelt.as_view(), name='coding_thekuiperbelt'),
]
