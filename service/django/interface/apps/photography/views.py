from django.shortcuts import render
from django.views.generic import TemplateView


class SpaceshipEarth(TemplateView):

    def get(self, errors=False, *args, **kwargs):
        context = {}
        return render(self.request, 'spaceshipearth.html', context)
