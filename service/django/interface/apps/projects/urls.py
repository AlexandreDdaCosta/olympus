from django.urls import path

from interface.apps.projects.views import TheKuiperBelt

urlpatterns = [
    path(r'', TheKuiperBelt.as_view(), name='projects_thekuiperbelt'),
]
