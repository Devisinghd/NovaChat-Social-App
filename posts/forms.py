from django import forms
from .models import Post, Comments

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['image', 'caption', 'title']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ('body',)
        exclude = ('posted_by', 'post')