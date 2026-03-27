from django.http import HttpResponse, Http404
from django.views.decorators.cache import cache_control
from django.conf import settings
from google.cloud import storage
import logging
import os

logger = logging.getLogger(__name__)

@cache_control(max_age=3600)  # Cache for 1 hour
def serve_image(request, file_path):
    """
    Serve media files from Google Cloud Storage through Django.
    Handles products/, aspect_icons/, and other media folders.
    This bypasses the domain restriction by using the service account.
    """
    bucket_name = settings.GS_BUCKET_NAME
    if not bucket_name:
        logger.error("GS_BUCKET_NAME not configured")
        raise Http404("Storage not configured")
    
    try:
        # Initialize the Google Cloud Storage client
        client = storage.Client(project=settings.GS_PROJECT_ID)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        
        # Check if the file exists
        if not blob.exists():
            logger.warning(f"File not found in bucket: {file_path}")
            raise Http404("File not found")
        
        # Download the file content
        content = blob.download_as_bytes()
        
        # Determine content type based on file extension
        content_type = 'application/octet-stream'
        file_extension = file_path.lower().split('.')[-1] if '.' in file_path else ''
        
        content_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml',
            'bmp': 'image/bmp',
            'ico': 'image/x-icon'
        }
        
        content_type = content_type_map.get(file_extension, 'application/octet-stream')
        
        # Create the response
        response = HttpResponse(content, content_type=content_type)
        response['Content-Length'] = len(content)
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
        
        # Add caching headers
        response['Cache-Control'] = 'public, max-age=3600'
        
        logger.info(f"Successfully served file: {file_path}")
        return response
        
    except Exception as e:
        logger.error(f"Error serving file {file_path}: {str(e)}")
        raise Http404("Error loading file")
