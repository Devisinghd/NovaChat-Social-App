from django.shortcuts import redirect, render
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
            return redirect('users/index')  # Redirect to the user's index page after creating the post
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})