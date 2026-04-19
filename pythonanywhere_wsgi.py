# This file contains the WSGI configuration required to serve up your
# Django application on PythonAnywhere.
#
# IMPORTANT: You must copy the contents of this file and paste it into
# the WSGI configuration file on your PythonAnywhere dashboard.
# (Web tab -> WSGI configuration file)

import os
import sys
from dotenv import load_dotenv

# REPLACE 'yourusername' with your actual PythonAnywhere username
# REPLACE 'UNIBUZZ' with the name of the folder where your code lives on PythonAnywhere
path = '/home/yourusername/UNIBUZZ'
if path not in sys.path:
    sys.path.insert(0, path)

# Load environment variables from .env file
env_path = os.path.join(path, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Set environment variable to tell django where your settings module is
os.environ['DJANGO_SETTINGS_MODULE'] = 'unibuzz_project.settings'

# Initialize Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
