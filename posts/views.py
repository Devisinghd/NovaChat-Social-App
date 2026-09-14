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
    return render(request, 'posts/feed.html', {'posts': posts})

def like_post(request):
    posts = request.POST.get('post_id')
    post = get_object_or_404(Post, id=posts)
    if post.liked_by.filter(id=request.user.id).exists():
        post.liked_by.remove(request.user)
    else:
        post.liked_by.add(request.user)
    return redirect('feed')