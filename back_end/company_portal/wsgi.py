"""
WSGI config for company_portal project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Determine settings module based on environment
if 'WEBSITE_HOSTNAME' in os.environ:
    # Azure App Service
    settings_module = 'company_portal.azure_settings'
elif 'GOOGLE_CLOUD_PROJECT' in os.environ:
    # Google Cloud Platform
    settings_module = 'company_portal.gcp_settings'
else:
    # Local development
    settings_module = 'company_portal.settings'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

application = get_wsgi_application()
