from django.shortcuts import render

from .forms import LoginForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
# Create your views here.

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = authenticate(request, username=data['username'], password=data['password'])
            if user:
                login(request, user)
                return HttpResponse("Login successful!")
            else:
                return HttpResponse("Invalid credentials. Please try again.")
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return render(request, 'users/logout.html')

@login_required
def index(request):
    return render(request, 'users/index.html')

