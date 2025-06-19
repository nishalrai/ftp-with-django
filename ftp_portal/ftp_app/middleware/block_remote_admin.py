# ftp_app/middleware/block_remote_admin.py
from django.http import HttpResponseForbidden

class BlockRemoteAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            remote_ip = request.META.get('REMOTE_ADDR')
            if remote_ip not in ['127.0.0.1', '::1']:  # Only allow localhost
                return HttpResponseForbidden("Admin access restricted to localhost.")
        return self.get_response(request)