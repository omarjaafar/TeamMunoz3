from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Message
from accounts.models import Profile

# Create your views here.
def index(request):
    template_data = {}
    template_data['user'] = request.user
    template_data['title'] = 'Messages'
    template_data['messages'] = request.user.received_messages.all() if request.user.is_authenticated else []
    # render the messages listing using the home app's template
    return render(request, 'home/recruiter_messages.html', {'template_data': template_data})

@login_required
def send_message(request):
    if request.method == 'POST':
        recipient_username = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        parent_id = request.POST.get('parent_id')

        try:
            recipient = User.objects.get(username=recipient_username)
            # enforce permissions: recruiters can start threads; job seekers can only reply
            sender_profile = getattr(request.user, 'profile', None)
            sender_role = sender_profile.role if sender_profile else None

            # if sender is a job seeker, ensure recipient has previously messaged them (a reply)
            if sender_role == Profile.JOB_SEEKER:
                # allow replies if parent_id provided or the recipient previously messaged them
                prior = False
                if parent_id:
                    # ensure parent exists and recipient is participant
                    try:
                        parent = Message.objects.get(id=parent_id)
                        # allow reply if the current user is either parent.sender or parent.recipient
                        prior = (parent.sender == recipient and parent.recipient == request.user) or (parent.sender == request.user and parent.recipient == recipient)
                    except Message.DoesNotExist:
                        prior = False
                else:
                    prior = Message.objects.filter(sender=recipient, recipient=request.user).exists()

                if not prior:
                    messages.error(request, "As a job seeker you cannot start a new conversation. Reply to a message first.")
                    return redirect('recruiter.messages')

            # create the message (attach parent if provided)
            msg_kwargs = {
                'sender': request.user,
                'recipient': recipient,
                'subject': subject,
                'body': body,
            }
            if parent_id:
                try:
                    parent = Message.objects.get(id=parent_id)
                    msg_kwargs['parent'] = parent
                except Message.DoesNotExist:
                    pass

            message = Message.objects.create(**msg_kwargs)
            messages.success(request, "Message sent successfully.")
        except User.DoesNotExist:
            messages.error(request, "Recipient does not exist.")

    # after sending, redirect back to the recruiter's messages page
    return redirect('recruiter.messages')

@login_required
def view_message(request, message_id):
    try:
        message = Message.objects.get(id=message_id, recipient=request.user)
        message.read = True
        message.save()
        template_data = {
            'title': 'View Message',
            'message': message
        }
        # reuse the home app's messages template for display
        return render(request, 'home/recruiter_messages.html', {'template_data': template_data})
    except Message.DoesNotExist:
        messages.error(request, "Message not found.")
        return redirect('messages.index')

@login_required
def delete_message(request, message_id):
    try:
        message = Message.objects.get(id=message_id, recipient=request.user)
        message.delete()
        messages.success(request, "Message deleted successfully.")
    except Message.DoesNotExist:
        messages.error(request, "Message not found.")
    return redirect('recruiter.messages')

