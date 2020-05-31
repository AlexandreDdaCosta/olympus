from django.conf.urls import url

from interface.apps.coding.views import TheKuiperBelt

urlpatterns = [
    url(r'', TheKuiperBelt.as_view(), name='coding_thekuiperbelt'),
]
