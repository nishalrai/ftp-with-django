from django.urls import path
from . import views

urlpatterns = [
    # Core file operations
    path('files/', views.file_list, name='file_list'),
    path('download/<path:file_name>/', views.download_file, name='download_file'),
    path('share/<uuid:uuid>/', views.share_file, name='share_file'),

    # User authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),   # Custom login view
    path('logout/', views.logout_view, name='logout'),
    path('delete-user/', views.delete_user, name='delete_user'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
]
