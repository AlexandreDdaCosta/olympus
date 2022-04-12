from django.conf.urls import path

from interface.apps.coding.views import TheKuiperBelt

urlpatterns = [
    path(r'', TheKuiperBelt.as_view(), name='coding_thekuiperbelt'),
]
