from django.shortcuts import render, redirect
import secrets
import logging
from .forms import LoginForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm
from .models import Profile, Follow, EmailVerificationCode
from .forms import UserEditForm, ProfileEditForm, EmailVerificationForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Exists, OuterRef
from django.conf import settings
from django.contrib import messages, sessions
from django.db import transaction
from django.contrib.auth.hashers import check_password, make_password
from django.template.loader import render_to_string

from posts.models import Post

logger = logging.getLogger(__name__)
# Create your views here.

def register(request):
    if request.user.is_authenticated:
        return redirect('feed')
    user_form = UserRegistrationForm
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST or None)
        if user_form.is_valid():
            user_form.check_passwords()
            new_user = user_form.save(commit=False)
            if not settings.EMAIL_VERIFICATION:
                new_user.is_active = True
                new_user.set_password(user_form.cleaned_data['password'])
                new_user.save()
                messages.success(request,'Account created successfully. You may now log in.')
                return redirect('login')

            new_user.is_active = False
            new_user.set_password(user_form.cleaned_data["password"])

            try:
                verification_code = f'{secrets.randbelow(1_000_000):06d}'
                with transaction.atomic():
                    new_user.save()
                    EmailVerificationCode.objects.update_or_create(
                        user=new_user,
                        defaults={
                            'code_hash':
                            make_password(verification_code),
                            'expires_at':
                            EmailVerificationCode.expiry_time(settings.EMAIL_OTP_EXPIRY_MINUTES),
                            'attempts': 0,
                        },
                    )

                    html_message = render_to_string('users/email_verification.html', {
                        'user': new_user,
                        'verification_code': verification_code,
                        'expiry_minutes': settings.EMAIL_OTP_EXPIRY_MINUTES,
                    })
                    plain_message = (
                        f'Hi {new_user}, your Novachat email verification code is '
                        f'{verification_code}. It expires in {settings.EMAIL_OTP_EXPIRY_MINUTES} minutes.'
                    )
                    new_user.email_user(
                        subject='Your Novachat email verification code',
                        message=plain_message,
                        html_message=html_message,
                        fail_silently=False,
                    )
                    
                request.session['pending_verification_user_id'] = new_user.pk
                messages.success(request,'Account created successfully. Check your email to activate the account')
                return redirect ('email_verification_sent')
            except Exception:
                logger.exception('Failed to sent verification email for user %s.',new_user.username)
                messages.error(request, 'We could not send verification code, please try again later')
                return redirect('register')
            
    return render(request, 'users/register.html', {'user_form': user_form})

def email_verification(request):
    user_id = request.session.get('pending_verification_user_id')
    user = User.objects.filter(pk=user_id,is_active=False).first()

    if user is None:
        return redirect('email_verification_failed')

    form = EmailVerificationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        verification = EmailVerificationCode.objects.filter(user=user).first()
        if verification and verification.is_expired():
            verification.delete()
            form.add_error('code','That code is invalid or expired.')
        elif verification and verification.attempts >= 5:
            verification.delete()
            form.add_error('code','Too many incorrect attempts. Register again to receive a new code.')
        elif verification and check_password(form.cleaned_data['code'],verification.code_hash):
            user.is_active = True
            user.save(update_fields=['is_active'])
            verification.delete()
            request.session.pop('pending_verification_user_id',None)
            Profile.objects.create(user=user)
            messages.success(request,'Your email has been verified successfully. You may now log in.')
            return redirect('email_verification_success')
        else:
            if verification:
                verification.attempts += 1
                if verification.attempts >= 5:
                    verification.delete()
                    form.add_error('code','Too many incorrect attempts. Register again to receive a new code.')
                else:
                    verification.save(update_fields=['attempts'])
                    form.add_error('code','That code is invalid or expired.')
            else:
                form.add_error('code','That code is invalid or expired.')
    return render(request, 'users/email_verification_sent.html',{'form':form,'expiry_minutes':settings.EMAIL_OTP_EXPIRY_MINUTES,})

def email_verification_sent(request):
    return email_verification(request)

def email_verification_success(request):
    return render(request, 'users/email_verification_success.html')

def email_verification_failed(request):
    return render(request, 'users/email_verification_failed.html')


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
                form.add_error('username', 'Invalid credentials. Please try again.')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

@require_http_methods(["GET", "POST"])
def user_logout(request):
    logout(request)
    return render(request, 'users/logout.html')


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