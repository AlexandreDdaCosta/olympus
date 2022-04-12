from django.urls import path

from interface.apps.photography.views import SpaceshipEarth

urlpatterns = [
    path(r'', SpaceshipEarth.as_view(), name='photography_spaceshipearth'),
]
