from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import BooleanField, Count, Exists, OuterRef, Prefetch, Value
from django.shortcuts import get_object_or_404, redirect, render

from .models import Comments, Post
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from users.models import Follow
# Create your views here.

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('feed')
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})

def feed(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect('login')
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            post_id = request.POST.get('post_id')
            post = get_object_or_404(Post, id=post_id)
            new_comment.post = post
            new_comment.posted_by = request.user.username
            new_comment.author = request.user
            new_comment.save()
            return redirect('feed')
        else:
            print(comment_form.errors)
    else:
        comment_form = CommentForm()
    liked_posts = Post.liked_by.through.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk,
    )
    recent_comments = Comments.objects.select_related(
        'author',
        'author__profile',
    ).order_by('-created_at', '-pk')[:2]
    if request.user.is_authenticated:
        following_author = Exists(Follow.objects.filter(
            follower=request.user,
            following_id=OuterRef('user_id'),
        ))
    else:
        following_author = Value(False, output_field=BooleanField())
    post_list = (
        Post.objects.select_related('user', 'user__profile')
        .annotate(
            like_count=Count('liked_by', distinct=True),
            comment_count=Count('comments', distinct=True),
            is_liked=Exists(liked_posts),
            is_following_author=following_author,
        )
        .prefetch_related(
            Prefetch('comments', queryset=recent_comments, to_attr='recent_comments')
        )
        .order_by('-created_at', '-pk')
    )
    posts = Paginator(post_list, 10).get_page(request.GET.get('page'))
    logged_in_user = request.user
    return render(request, 'posts/feed.html', {
        'posts': posts,
        'logged_in_user': logged_in_user,
        'comment_form': comment_form,
        'post_user': request.user.get_username(),
    })

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

def comments(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('user', 'user__profile')
        .annotate(like_count=Count('liked_by', distinct=True)),
        pk=post_id,
    )

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.posted_by = request.user.get_username()
            new_comment.author = request.user
            new_comment.save()
            return redirect('post_comments', post_id=post.pk)
    else:
        comment_form = CommentForm()

    post_comments = post.comments.select_related(
        'author',
        'author__profile',
    ).order_by('created_at', 'pk')
    return render(request, 'posts/comments.html', {
        'post': post,
        'comments': post_comments,
        'comment_form': comment_form,
    })