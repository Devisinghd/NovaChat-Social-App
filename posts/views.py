from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Post
from .forms import PostForm
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('users/index')
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})

def feed(request):
    posts = Post.objects.all()
    logged_in_user = request.user 
    return render(request, 'posts/feed.html', {'posts': posts, 'logged_in_user': logged_in_user})

@login_required
def like_post(request):
    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.liked_by.filter(id=request.user.id).exists():
        post.liked_by.remove(request.user)
        liked = False
    else:
        post.liked_by.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'count': post.liked_by.count()})