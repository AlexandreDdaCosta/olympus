from django.conf.urls import url

from interface.apps.photography.views import SpaceshipEarth

urlpatterns = [
    url(r'', SpaceshipEarth.as_view(), name='photography_spaceshipearth'),
]
