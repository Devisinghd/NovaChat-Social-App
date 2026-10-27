from django.db import models
from django.contrib.auth.models import User

class Thread(models.Model):
    # Ensures exactly two people belong to an Instagram DM thread
    participants = models.ManyToManyField(User, related_name='chat_threads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Changes whenever a new message updates the thread

    class Meta:
        ordering = ['-updated_at'] # Moves the most recently active chat to the top of the inbox

    def __str__(self):
        return f"Thread {self.id}"

class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_content = models.TextField()
    # Millisecond tracking ensures true timeline order for bubbles
    date = models.DateTimeField(auto_now_add=True) 

    class Meta:
        ordering = ('date',)

    def __str__(self):
        return f"{self.sender.username}: {self.chat_content[:20]}"
