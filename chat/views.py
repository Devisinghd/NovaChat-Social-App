from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Count, OuterRef, Subquery
from .models import Thread, Message
from users.models import Follow

@login_required
def chat_dashboard(request):
    # 1. Fetch all private conversations the user is a part of (Your Inbox)
    latest_messages = Message.objects.filter(thread_id=OuterRef('pk')).order_by('-date')
    my_threads = request.user.chat_threads.annotate(
        last_message=Subquery(latest_messages.values('chat_content')[:1]),
        last_message_sender=Subquery(latest_messages.values('sender__username')[:1]),
        last_message_date=Subquery(latest_messages.values('date')[:1]),
    ).prefetch_related('participants__profile')

    # 2. Fetch followings (to let users start new chats from their list)
    chat_partners = Follow.objects.filter(follower=request.user).select_related(
        'following',
        'following__profile',
    )

    return render(request, 'chat/chat_dashboard.html', {
        'my_threads': my_threads,
        'chat_partners': chat_partners
    })

@login_required
def get_or_create_thread(request, user_id):
    """ Finds or creates a unique thread containing exactly request.user and target user """
    other_user = get_object_or_404(User, id=user_id)

    if other_user == request.user:
        return redirect('chat_dashboard')

    # Look for a thread containing exactly these two participants
    threads = Thread.objects.annotate(num_participants=Count('participants')).filter(
        num_participants=2,
        participants=request.user
    ).filter(
        participants=other_user
    )

    if threads.exists():
        thread = threads.first()
    else:
        # Create a new private thread if none exists
        thread = Thread.objects.create()
        thread.participants.add(request.user, other_user)

    return redirect('chatroom', thread_id=thread.id)

@login_required
def chatroom(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)

    # Security block: prevent random users from guessing thread IDs
    if request.user not in thread.participants.all():
        return redirect('chat_dashboard')

    # Identify the other person's name for the header title
    recipient = thread.participants.exclude(id=request.user.id).first()

    # Fetch historical messages to populate the thread on load
    chat_messages = thread.messages.select_related('sender')

    return render(request, 'chat/room.html', {
        'thread': thread,
        'recipient': recipient,
        'chat_messages': chat_messages
    })
