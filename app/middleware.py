"""
Custom middleware for serving media files in production
"""
import os
from django.conf import settings
from django.http import HttpResponse, Http404
from django.utils.deprecation import MiddlewareMixin
from django.views.static import serve
import mimetypes


class MediaFileMiddleware(MiddlewareMixin):
    """
    Middleware to serve media files in production when DEBUG=False
    This is needed for platforms like Render that don't serve media files by default
    """
    
    def process_request(self, request):
        """
        Check if the request is for a media file and serve it if found
        """
        # Only handle media file requests
        if not request.path.startswith(settings.MEDIA_URL):
            return None
        
        # In development, let Django handle it normally
        if settings.DEBUG:
            return None
        
        # Extract the file path from the URL
        file_path = request.path[len(settings.MEDIA_URL):]
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        # Check if file exists
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            raise Http404("Media file not found")
        
        # Serve the file
        try:
            return serve(request, file_path, document_root=settings.MEDIA_ROOT)
        except Exception:
            raise Http404("Error serving media file")
