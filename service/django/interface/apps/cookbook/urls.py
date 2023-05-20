from django.urls import path

from interface.apps.cookbook.views import TheFamilyCookbook

urlpatterns = [
    path(r'', TheFamilyCookbook.as_view(), name='thefamilycookbook'),
]
