"""
URL configuration for company_portal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from main.views.health import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('main.urls')),
    path('health/', health_check, name='health-check'),
]

# Add media proxy when using Google Cloud Storage
if hasattr(settings, 'GS_BUCKET_NAME') and settings.GS_BUCKET_NAME:
    from main.views.media_proxy import serve_image
    urlpatterns += [
        re_path(r'^(?P<file_path>products/.*)$', serve_image, name='products-proxy'),
    ]

# In development, serve local media files via Django's static() helper so
# MEDIA_URL ('/media/') is available at the development server.
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
