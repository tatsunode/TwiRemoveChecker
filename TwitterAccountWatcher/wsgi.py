"""
WSGI config for TwitterAccountWatcher project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""
#/usr/bin/python3

import os
import sys
import site

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
site.addsitedir(os.path.join(PROJECT_ROOT, 'ENV', 'lib', 'python3.5', 'site-packages'))
sys.path.insert(0, PROJECT_ROOT)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TwitterAccountWatcher.settings')

application = get_wsgi_application()
