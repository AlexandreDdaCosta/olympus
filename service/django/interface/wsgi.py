#!/usr/bin/env python3
import os, sys
sys.path.append('/usr/local/lib/python3.4/dist-packages')
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interface.settings")
django.setup()
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
