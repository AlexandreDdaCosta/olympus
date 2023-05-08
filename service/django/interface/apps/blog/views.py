from django.shortcuts import render
from django.views.generic import TemplateView


class TheZodiacalLight(TemplateView):

    def get(self, errors=False, *args, **kwargs):
        context = {}
        return render(self.request, 'thezodiacallight.html', context)
