import os
from django.conf import settings
from django import setup
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from django.contrib.auth.models import User
from ftp_app.models import FTPUser

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ftp_portal.settings')
if not settings.configured:
    setup()

def start_ftp_server():
    authorizer = DummyAuthorizer()
    
    ftp_users = FTPUser.objects.all()
    for ftp_user in ftp_users:
        user = ftp_user.user
        if user.is_active:
            authorizer.add_user(
                user.username,
                user.password,
                ftp_user.ftp_directory,
                perm='elradfmwMT'
            )
    
    authorizer.add_anonymous(os.getcwd())
    
    handler = FTPHandler
    handler.authorizer = authorizer
    handler.banner = "pyftpdlib based FTP server ready."
    
    address = ('', 2121)
    server = FTPServer(address, handler)
    
    server.max_cons = 256
    server.max_cons_per_ip = 5
    
    server.serve_forever()

if __name__ == '__main__':
    start_ftp_server()