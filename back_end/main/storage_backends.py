from storages.backends.gcloud import GoogleCloudStorage
from django.conf import settings


class ProxyGoogleCloudStorage(GoogleCloudStorage):
    """
    Custom Google Cloud Storage backend that generates proxy URLs
    instead of direct GCS URLs to work with domain restrictions.
    """
    
    def url(self, name):
        """
        Override the URL method to return proxy URLs instead of direct GCS URLs.
        This allows us to serve files through Django while bypassing domain restrictions.
        """
        # Return the proxy URL path instead of the full GCS URL
        return f"/{name}"
