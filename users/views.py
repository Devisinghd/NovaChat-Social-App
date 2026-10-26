from django.shortcuts import render, redirect

from .forms import LoginForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm
from .models import Profile, Follow
from .forms import UserEditForm, ProfileEditForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Exists, OuterRef

from posts.models import Post
# Create your views here.

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = authenticate(request, username=data['username'], password=data['password'])
            if user:
                login(request, user)
                return redirect('feed')
            else:
                return HttpResponse("Invalid credentials. Please try again.")
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

@require_http_methods(["GET", "POST"])
def user_logout(request):
    logout(request)
    return render(request, 'users/logout.html')

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            user_form.check_passwords()
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            Profile.objects.create(user=new_user)
            return render(request, 'users/register_done.html', {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, 'users/register.html', {'user_form': user_form})

@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    return render(request, 'users/edit.html', {'user_form': user_form, 'profile_form': profile_form})



@login_required(login_url='login')
def profile(request, username=None):
    profile_user = request.user if username is None else get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile.objects.select_related('user'), user=profile_user)
    followers = Follow.objects.filter(following=profile_user).select_related(
        'follower',
        'follower__profile',
    )
    following = Follow.objects.filter(follower=profile_user).select_related(
        'following',
        'following__profile',
    )
    is_following = Follow.objects.filter(
        follower=request.user,
        following=profile_user,
    ).exists()
    posts = Post.objects.filter(user=profile_user).order_by('-created_at')
    return render(request, 'users/profile.html', {
        'profile_user': profile_user,
        'is_following': is_following,
        'is_own_profile': profile_user == request.user,
        'profile': profile,
        'followers': followers,
        'following': following,
        'followers_count': followers.count(),
        'following_count': following.count(),
        'posts': posts,
    })

@login_required(login_url='login')
def settings_page(request):
    return render(request, 'users/settings.html')


@login_required(login_url='login')
@require_POST
def toggle_follow(request, username):
    target = get_object_or_404(User, username=username)

    if target != request.user:
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target,
        )
        if not created:
            follow.delete()

    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect('user_profile', username=username)

@login_required(login_url='login')
def followers_list(request, username):
    profile_user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(following=profile_user).select_related(
        'follower',
        'follower__profile',
    ).annotate(
        is_following=Exists(Follow.objects.filter(
            follower=request.user,
            following_id=OuterRef('follower_id'),
        ))
    )
    return render(request, 'users/follower_list.html', {
        'profile_user': profile_user,
        'followers': followers,
    })

@login_required(login_url='login')
def following_list(request, username):
    profile_user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(follower=profile_user).select_related(
        'following',
        'following__profile',
    ).annotate(
        is_following=Exists(Follow.objects.filter(
            follower=request.user,
            following_id=OuterRef('following_id'),
        ))
    )
    return render(request, 'users/following_list.html', {
        'profile_user': profile_user,
        'following': following,
    })

@login_required(login_url='login')
@require_POST
def remove_follower(request, username):
    profile_user = get_object_or_404(User, username=username)
    if request.user != profile_user:
        return redirect('user_profile', username=username)

    follower = get_object_or_404(User, username=request.POST.get('follower'))
    Follow.objects.filter(follower=follower, following=profile_user).delete()

    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect('followers_list', username=username)

def post_user_profile_search(request, username):
    get_object_or_404(User, username=username)
    return redirect('user_profile', username=username)