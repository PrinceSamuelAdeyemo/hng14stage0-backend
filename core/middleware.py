from django.utils.deprecation import MiddlewareMixin

class DisableCSRFForAPI(MiddlewareMixin):
    """
    Disable CSRF protection for API endpoints that start with /api/
    """
    def process_request(self, request):
        if request.path.startswith('/api/'):
            request.csrf_processing_done = True
        return None
