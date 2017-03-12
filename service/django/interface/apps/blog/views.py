from django.shortcuts import render

class FrontPage():

    def get(self, errors=False, *args, **kwargs):
        context = {}
        return render(self.request,'/frontpage.html',context)
