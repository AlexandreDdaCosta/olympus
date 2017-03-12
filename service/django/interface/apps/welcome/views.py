from django.shortcuts import render
from django.views.generic import TemplateView

class Home(TemplateView):

    def get(self, errors=False, *args, **kwargs):
        context = {}
        return render(self.request,'home.html',context)

