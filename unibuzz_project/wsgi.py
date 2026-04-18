"""
WSGI config for unibuzz_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

import sys
import traceback
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unibuzz_project.settings')

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    app = application
except Exception as e:
    # If Django fails to start, return the traceback to the browser
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return [traceback.format_exc().encode('utf-8')]
    app = application
