from django.urls import path

from interface.apps.security_analyzer.views import SecurityAnalyzer

urlpatterns = [
    path(r'', SecurityAnalyzer.as_view(), name='securityanalyzer'),
]
