from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .permissions import IsAuthenticated, IsManufacturingUser
import os
import uuid
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)


class MediaImagesView(APIView):
    """
    GET: List images in the 'products/' storage prefix.
    POST: Upload an image to the 'products/' prefix.

    GET is available to any authenticated user. POST requires a manufacturing
    user (i.e. users allowed to create/update products).
    """
    # Max upload size: 5MB
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        - GET requests are allowed for any authenticated user.
        - POST requests are restricted to manufacturing users.
        """
        if self.request.method == 'POST':
            # For uploads, user must be authenticated AND a manufacturing user.
            return [IsAuthenticated(), IsManufacturingUser()]
        return [IsAuthenticated()]

    def get(self, request):
        images = []
        prefix = 'products/'

        bucket_name = getattr(settings, 'GS_BUCKET_NAME', None)
        if bucket_name:
            # Google Cloud Storage: list blobs under the prefix
            try:
                from google.cloud import storage
                client = storage.Client(project=getattr(settings, 'GS_PROJECT_ID', None))
                bucket = client.bucket(bucket_name)
                blobs = client.list_blobs(bucket_name, prefix=prefix)
                for blob in blobs:
                    # Only include actual files that look like images, ignore "folders".
                    content_type = (blob.content_type or '').lower()
                    if not blob.name.endswith('/') and (content_type.startswith('image/') or os.path.splitext(blob.name)[1].lower() in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
                        url = default_storage.url(blob.name)
                        images.append({'name': blob.name, 'url': request.build_absolute_uri(url)})
            except Exception as e:
                logger.exception('Failed to list images from GCS')
                return Response({'error': 'Failed to list images'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Local filesystem: walk MEDIA_ROOT/products/
            media_root = getattr(settings, 'MEDIA_ROOT', None)
            if not media_root:
                return Response({'images': []})
            products_dir = os.path.join(media_root, 'products')
            if not os.path.exists(products_dir):
                try:
                    os.makedirs(products_dir) # Create directory if it doesn't exist
                except OSError:
                    logger.error("Failed to create local media directory for products.")
                    return Response({'error': 'Failed to create media directory.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            for root, _, files in os.walk(products_dir):
                for fname in files:
                    relpath = os.path.relpath(os.path.join(root, fname), media_root).replace('\\', '/')
                    url = default_storage.url(relpath)
                    images.append({'name': relpath, 'url': request.build_absolute_uri(url)})

        return Response({'images': images}, status=status.HTTP_200_OK)

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided (expect multipart form-data with key "file").'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded = request.FILES['file']
        if uploaded.size > self.MAX_UPLOAD_SIZE:
            return Response({'error': f'File too large. Max {self.MAX_UPLOAD_SIZE // (1024*1024)}MB.'}, status=status.HTTP_400_BAD_REQUEST)

        content_type = getattr(uploaded, 'content_type', '') or ''
        if not content_type.startswith('image/'):
            # allow checking by extension as a fallback
            ext = os.path.splitext(getattr(uploaded, 'name', '') or '')[1].lower()
            if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'):
                return Response({'error': 'Uploaded file is not an image.'}, status=status.HTTP_400_BAD_REQUEST)

        # generate a safe filename under products/
        # Use a library to secure the filename against path traversal.
        safe_basename = secure_filename(uploaded.name)
        safe_name = f"products/{uuid.uuid4().hex}_{safe_basename}"

        try:
            saved_name = default_storage.save(safe_name, uploaded)
            url = default_storage.url(saved_name)
            return Response({'name': saved_name, 'url': request.build_absolute_uri(url)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception('Failed to save uploaded image')
            return Response({'error': 'Failed to save uploaded image'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
