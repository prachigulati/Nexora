import time
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import json

class TimeTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track time spent on the site by users
    """
    
    def process_request(self, request):
        # Store start time for this request
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        # Calculate time spent if this was a time tracking request
        if hasattr(request, 'start_time'):
            time_spent = time.time() - request.start_time
            
            # If this is an AJAX request for time tracking, return the time
            if (request.path == '/api/track-time/' and 
                request.method == 'POST' and 
                hasattr(request, 'user') and 
                request.user.is_authenticated):
                
                try:
                    # Get the time data from the request body
                    data = json.loads(request.body.decode('utf-8'))
                    time_spent = data.get('time_spent', 0)
                    
                    # Here you could save the time to the database
                    # For now, we'll just return a success response
                    return JsonResponse({'status': 'success', 'time_tracked': time_spent})
                    
                except (json.JSONDecodeError, KeyError):
                    return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
        
        return response
