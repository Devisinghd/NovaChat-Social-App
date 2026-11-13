from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import Thread, Message
from users.models import Follow

@login_required
def chat_dashboard(request):
    # 1. Fetch all private conversations the user is a part of inbox
    my_threads = []
    candidate_threads = Thread.objects.filter(participants=request.user).prefetch_related(
        'participants__profile',
        'messages__sender',
    ).order_by('-updated_at')

    for thread in candidate_threads:
        if len(thread.participants.all()) != 2:
            continue

        latest_message = thread.messages.order_by('-date', '-pk').first()
        thread.last_message = latest_message.chat_content if latest_message else None
        thread.last_message_sender = latest_message.sender.username if latest_message else None
        thread.last_message_date = latest_message.date if latest_message else None
        my_threads.append(thread)

    my_threads.sort(
        key=lambda thread: thread.last_message_date or thread.updated_at,
        reverse=True,
    )

    # Fetch people on either side of the follow relationship for starting chats
    incoming_partner_ids = Follow.objects.filter(following=request.user).values_list(
        'follower_id', flat=True,
    )
    outgoing_partner_ids = Follow.objects.filter(follower=request.user).values_list(
        'following_id', flat=True,
    )
    partner_ids = set(incoming_partner_ids) | set(outgoing_partner_ids)
    chat_partners = User.objects.filter(pk__in=partner_ids).select_related('profile').order_by('username')

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
