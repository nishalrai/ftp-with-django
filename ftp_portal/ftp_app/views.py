import os, shutil, posixpath, urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import FileResponse, Http404
from django.utils import timezone
from .models import FTPUser, ShareLink
from django.contrib.auth.models import User
from datetime import timedelta
from django.db import IntegrityError, transaction
import logging


logger = logging.getLogger(__name__)


def register(request):
    if request.method != 'POST':
        return render(request, 'register.html')

    username = request.POST.get('username')
    email = request.POST.get('email')
    password = request.POST.get('password')
    password_confirm = request.POST.get('password_confirm')

    # Basic validation
    if not username or len(username) > 150:
        messages.error(request, 'Username is required and must be 150 characters or fewer.')
    elif User.objects.filter(username=username).exists():
        messages.error(request, 'This username is already taken.')
    elif not email:
        messages.error(request, 'Email is required.')
    elif User.objects.filter(email=email).exists():
        messages.error(request, 'This email is already registered.')
    elif len(password) < 8:
        messages.error(request, 'Password must be at least 8 characters long.')
    elif password != password_confirm:
        messages.error(request, 'Passwords do not match.')
    else:
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email, password=password)

                ftp_dir = os.path.join(settings.MEDIA_ROOT, 'ftp', username)
                if not os.path.exists(ftp_dir):
                    os.makedirs(ftp_dir)

                ftp_user, created = FTPUser.objects.get_or_create(user=user, defaults={'ftp_directory': ftp_dir})
                if not created:
                    messages.error(request, 'An FTP user already exists for this account.')
                    return render(request, 'register.html')

                # Do NOT log in the user automatically here
                messages.success(request, 'Registration successful! Please login now.')
                return redirect('login')  # Redirect to login page

        except IntegrityError as e:
            messages.error(request, 'Integrity error during registration. Please try again later.')
            print("IntegrityError during registration:", e)
        except Exception as e:
            messages.error(request, 'An unexpected error occurred during registration. Please try again.')
            print("Unexpected error during registration:", e)

    return render(request, 'register.html')


def login_view(request):
    if request.user.is_authenticated:
        # Already logged in, redirect to file management page
        return redirect('file_list')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('file_list')  # Redirect to files page after login
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def delete_user(request):
    if request.method == 'POST':
        user = request.user
        ftp_user = FTPUser.objects.get(user=user)
        ftp_dir = ftp_user.ftp_directory
        try:
            if os.path.exists(ftp_dir):
                shutil.rmtree(ftp_dir)
            ftp_user.delete()
            user.delete()
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error deleting account: {str(e)}')
    return redirect('dashboard')

@login_required
def file_list(request):
    # Get user's FTP directory
    try:
        ftp_user = FTPUser.objects.get(user=request.user)
        user_ftp_dir = ftp_user.ftp_directory
    except FTPUser.DoesNotExist:
        messages.error(request, 'FTP user profile not found. Please contact support.')
        return redirect('dashboard')

    # Recursively build a nested file/folder tree
    def build_file_tree(root_path):
        tree = []
        dir_dict = {}

        for root, dirs, filenames in os.walk(root_path, topdown=True):
            rel_root = os.path.relpath(root, root_path)
            if rel_root in ('.', './'):
                rel_root = ''

            if rel_root:
                parts = rel_root.split(os.sep)
                current = tree
                for i, part in enumerate(parts):
                    path_so_far = os.sep.join(parts[:i + 1])
                    dir_entry = next((item for item in current if item['name'] == path_so_far and item['is_dir']), None)
                    if not dir_entry:
                        dir_entry = {
                            'name': path_so_far,
                            'is_dir': True,
                            'size': 0,
                            'children': []
                        }
                        current.append(dir_entry)
                        dir_dict[path_so_far] = dir_entry
                    current = dir_entry['children']

            current = dir_dict.get(rel_root, tree)
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.join(rel_root, filename) if rel_root else filename
                current.append({
                    'name': rel_path,
                    'is_dir': False,
                    'size': os.path.getsize(file_path),
                    'children': []
                })

        return sorted(tree, key=lambda x: (not x['is_dir'], x['name'].lower()))

    files = build_file_tree(user_ftp_dir)

    if request.method == 'POST':
        # Upload files or folders
        if 'upload' in request.POST:
            uploaded_files = request.FILES.getlist('uploads')
            if not uploaded_files:
                messages.error(request, 'No files selected for upload.')
            else:
                try:
                    for uploaded_file in uploaded_files:
                        relative_path = posixpath.normpath(uploaded_file.name).lstrip('/')
                        if '..' in relative_path or relative_path.startswith('/'):
                            messages.error(request, f'Invalid file path: {relative_path}')
                            continue
                        file_path = os.path.join(user_ftp_dir, relative_path)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, 'wb+') as destination:
                            for chunk in uploaded_file.chunks():
                                destination.write(chunk)
                    messages.success(request, 'Files uploaded successfully!')
                except Exception as e:
                    messages.error(request, f'Upload failed: {str(e)}')

        # Delete selected files/folders
        elif 'delete' in request.POST:
            selected_files = request.POST.getlist('selected_files')
            if not selected_files:
                messages.error(request, 'No files or folders selected.')
            else:
                try:
                    for file_name in selected_files:
                        try:
                            decoded_name = urllib.parse.unquote(file_name.encode('utf-8').decode('unicode_escape'))
                            file_path = os.path.normpath(os.path.join(user_ftp_dir, decoded_name))
                            if not file_path.startswith(user_ftp_dir):
                                messages.error(request, f'Invalid path: {decoded_name}')
                                continue
                            if os.path.exists(file_path):
                                if os.path.isdir(file_path):
                                    shutil.rmtree(file_path)
                                else:
                                    os.remove(file_path)
                            else:
                                messages.error(request, f'{decoded_name} does not exist.')
                        except Exception as e:
                            messages.error(request, f'Error deleting {file_name}: {str(e)}')
                except Exception as e:
                    messages.error(request, f'Deletion process failed: {str(e)}')

        # Rename selected files/folders
        elif 'rename' in request.POST:
            old_names = request.POST.getlist('old_names')
            new_names = request.POST.getlist('new_names')
            if not old_names or len(old_names) != len(new_names):
                messages.error(request, 'Invalid rename request.')
            else:
                try:
                    for old_name, new_name in zip(old_names, new_names):
                        old_name = urllib.parse.unquote(old_name.replace('\u002D', '-'))
                        new_name = new_name.strip()
                        if not new_name:
                            messages.error(request, f'New name cannot be empty for {old_name}.')
                            continue

                        # Extract original extension
                        _, ext = os.path.splitext(old_name)
                        # Append original extension to new_name
                        new_name_with_ext = new_name + ext

                        old_path = os.path.join(user_ftp_dir, old_name)
                        new_path = os.path.join(user_ftp_dir, new_name_with_ext)
                        if os.path.exists(old_path) and not os.path.exists(new_path):
                            os.makedirs(os.path.dirname(new_path), exist_ok=True)
                            os.rename(old_path, new_path)
                        else:
                            messages.error(request, f'Rename failed for {old_name}: Invalid name or file exists.')
                    messages.success(request, 'Selected items renamed successfully!')
                except Exception as e:
                    messages.error(request, f'Rename failed: {str(e)}')

        # Share files by generating share links
        elif 'share' in request.POST:
            selected_files = request.POST.getlist('selected_files')
            requires_auth = request.POST.get('requires_auth') == 'on'
            expiry_days = int(request.POST.get('expiry_days', 7))
            if not selected_files:
                messages.error(request, 'No files selected for sharing.')
            else:
                share_links = []
                try:
                    for file_name in selected_files:
                        file_name = urllib.parse.unquote(file_name.encode('utf-8').decode('unicode_escape'))
                        file_path = os.path.join(user_ftp_dir, file_name)
                        if os.path.exists(file_path) and os.path.isfile(file_path):
                            share_link = ShareLink.objects.create(
                                file_path=file_name,
                                user=request.user,
                                expires_at=timezone.now() + timedelta(days=expiry_days),
                                requires_auth=requires_auth
                            )
                            share_links.append(f"{request.build_absolute_uri('/share/')}{share_link.uuid}")
                        else:
                            messages.error(request, f'{file_name} does not exist.')
                    if share_links:
                        request.session['share_links'] = share_links
                        messages.success(request, 'Share links generated successfully!')
                except Exception as e:
                    messages.error(request, f'Share failed: {str(e)}')

        # Download selected file (only one allowed)
        elif 'download' in request.POST:
            selected_files = request.POST.getlist('selected_files')
            if not selected_files:
                messages.error(request, 'No files selected for download.')
            else:
                file_name = urllib.parse.unquote(selected_files[0].replace('\u002D', '-'))
                file_path = os.path.join(user_ftp_dir, file_name)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
                messages.error(request, f'{file_name} does not exist.')

        return redirect('file_list')

    share_links = request.session.pop('share_links', [])
    return render(request, 'file_list.html', {'files': files, 'share_links': share_links})

@login_required
def download_file(request, file_name):
    #file_name = urllib.parse.unquote(file_name.replace('\u002D', '-'))
    file_name = urllib.parse.unquote(file_name.encode('utf-8').decode('unicode_escape'))
    ftp_user = FTPUser.objects.get(user=request.user)
    file_path = os.path.join(ftp_user.ftp_directory, file_name)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
    raise Http404("File does not exist")

def share_file(request, uuid):
    share_link = get_object_or_404(ShareLink, uuid=uuid)
    if not share_link.is_valid():
        raise Http404("Share link has expired")
    
    if share_link.requires_auth and not request.user.is_authenticated:
        messages.error(request, 'Authentication required to access this file.')
        return redirect('login')
    
    ftp_user = FTPUser.objects.get(user=share_link.user)
    file_path = os.path.join(ftp_user.ftp_directory, share_link.file_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
    raise Http404("File does not exist")