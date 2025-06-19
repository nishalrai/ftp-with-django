# Empty forms.py as authentication will use Django's built-in forms

'''
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        min_length=8,
        help_text='Password must be at least 8 characters long.'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        label="Confirm Password",
        help_text='Re-enter your password to confirm.'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email'}),
        }
        help_texts = {
            'username': 'Choose a username (letters, digits, @/./+/-/_ only, max 150 characters).',
        }
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('Username is required.')
        if len(username) > 150:
            raise ValidationError('Username must be 150 characters or fewer.')
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('Email is required.')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords do not match.")
        return cleaned_data

class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter username'}),
        max_length=150,
        help_text='Enter your username.'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        help_text='Enter your password.'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise ValidationError('Invalid username or password.')
        return cleaned_data
'''
