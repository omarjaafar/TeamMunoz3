from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Message, EmailMessage
from django.db.models import Q
from accounts.models import Profile
from django.core.mail import send_mail
from django.conf import settings
import smtplib

# Create your views here.
def index(request):
    template_data = {}
    template_data['user'] = request.user
    template_data['title'] = 'Messages'

    if not request.user.is_authenticated:
        template_data['conversations'] = []
        return render(request, 'home/recruiter_messages.html', {'template_data': template_data})

    user = request.user
    # collect latest message per conversation partner
    from django.db.models import Q
    msgs = Message.objects.filter(Q(sender=user) | Q(recipient=user)).order_by('-timestamp')
    seen = set()
    conversations = []
    for m in msgs:
        partner = m.sender if m.sender != user else m.recipient
        if partner.id in seen:
            continue
        seen.add(partner.id)
        # count unread messages from partner to user
        unread_count = Message.objects.filter(sender=partner, recipient=user, read=False).count()
        conversations.append({
            'partner': partner,
            'latest': m,
            'unread': unread_count,
        })

    template_data['conversations'] = conversations
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

@login_required
def send_email(request):
    # Simple email send view using Django's send_mail
    if request.method == 'POST':
        recipient_email = request.POST.get('email') or request.POST.get('recipient_email')
        subject = request.POST.get('subject')
        message_body = request.POST.get('body')
        parent_id = request.POST.get('parent_id')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        # If replying to a thread, we can auto-fill subject from the parent if missing
        if parent_id and not subject:
            try:
                parent_obj = EmailMessage.objects.get(id=parent_id)
                subject = f"Re: {parent_obj.subject}" if parent_obj.subject else 'Re:'
            except EmailMessage.DoesNotExist:
                subject = subject

        if not (recipient_email and message_body and subject):
            messages.error(request, 'All fields are required to send an email.')
            return redirect('messages.send_email')

        try:
            # Use Django's send_mail; configuration controlled via settings.py
            send_mail(subject, message_body, from_email, [recipient_email], fail_silently=False)
            sent_ok = True
            error_text = None
            messages.success(request, 'Email sent successfully.')
        except Exception as e:
            sent_ok = False
            error_text = str(e)
            messages.error(request, f'An error occurred sending the email: {e}')

        # persist a record of the email we attempted to send
        try:
            recipient_user = None
            try:
                recipient_user = User.objects.get(email__iexact=recipient_email)
            except User.DoesNotExist:
                recipient_user = None

            em_kwargs = {
                'sender': request.user,
                'sender_email': request.user.email if getattr(request.user, 'email', None) else None,
                'recipient_user': recipient_user,
                'recipient_email': recipient_email,
                'subject': subject,
                'body': message_body,
                'sent_ok': sent_ok,
                'error': error_text if not sent_ok else None,
            }
            if parent_id:
                try:
                    parent_email = EmailMessage.objects.get(id=parent_id)
                    em_kwargs['parent'] = parent_email
                except EmailMessage.DoesNotExist:
                    pass

            EmailMessage.objects.create(**em_kwargs)
        except Exception:
            # non-fatal if persistence fails; we already attempted to send
            pass

        return redirect('messages.send_email')

    # GET: render a simple email form. Provide a dropdown of jobseekers (username + email).
    jobseekers = User.objects.filter(profile__role=Profile.JOB_SEEKER).exclude(email__isnull=True).exclude(email__exact='').order_by('username')
    return render(request, 'home/send_email.html', {'template_data': {'title': 'Send Email', 'jobseekers': jobseekers}})

from django.shortcuts import render
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

def send_mail_page(request):
    context = {}

    if request.method == 'POST':
        address = request.POST.get('address')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if address and subject and message:
            try:
                send_mail(subject, message, settings.EMAIL_HOST_USER, [address])
                context['result'] = 'Email sent successfully'
            except Exception as e:
                context['result'] = f'Error sending email: {e}'
        else:
            context['result'] = 'All fields are required'
    
    return render(request, "index.html", context)


@login_required
def email_inbox(request):
    # show emails sent to the logged-in user's email address or addressed to their user account
    user_email = request.user.email
    # include emails where the user is recipient (by user or by email) OR the user is the sender (so sent messages appear too)
    inbox_q = Q(recipient_user=request.user) | Q(sender=request.user)
    if user_email:
        inbox_q = inbox_q | Q(recipient_email__iexact=user_email)

    emails = EmailMessage.objects.filter(inbox_q).order_by('-timestamp')
    return render(request, 'home/email_inbox.html', {'emails': emails, 'template_data': {'title': 'Email Inbox'}})


@csrf_exempt
def receive_inbound_email(request):
    """
    Simple inbound webhook endpoint to record incoming emails.
    Accepts POST requests (e.g., from SendGrid Inbound Parse or similar) and creates an EmailMessage record.
    Expected form fields: 'from' (sender email), 'to' (recipient email), 'subject', 'text' or 'body'.
    WARNING: This endpoint is intentionally simple. In production you should validate source, sign requests, and protect it.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from_addr = request.POST.get('from') or request.POST.get('sender') or request.POST.get('From')
    to_addr = request.POST.get('to') or request.POST.get('recipient') or request.POST.get('To')
    subject = request.POST.get('subject') or ''
    body = request.POST.get('text') or request.POST.get('body') or request.POST.get('html') or ''

    if not to_addr:
        return JsonResponse({'error': 'to field required'}, status=400)

    recipient_user = None
    try:
        recipient_user = User.objects.get(email__iexact=to_addr)
    except User.DoesNotExist:
        recipient_user = None

    try:
        EmailMessage.objects.create(
            sender=None,
            sender_email=from_addr,
            recipient_user=recipient_user,
            recipient_email=to_addr,
            subject=subject,
            body=body,
            sent_ok=True,
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'status': 'ok'})


def _collect_thread(root):
    # Depth-first traversal collecting (message, depth)
    collected = []
    def dfs(msg, depth=0):
        collected.append((msg, depth))
        for child in msg.replies.order_by('timestamp').all():
            dfs(child, depth+1)
    dfs(root, 0)
    return collected


@login_required
def email_thread(request, email_id):
    try:
        email = EmailMessage.objects.get(id=email_id)
    except EmailMessage.DoesNotExist:
        messages.error(request, "Email not found.")
        return redirect('messages.email_inbox')

    # permission: allow if current user is sender, recipient_user, or recipient_email matches
    cur = request.user
    allowed = (email.sender == cur) or (email.recipient_user == cur) or (email.recipient_email and email.recipient_email.lower() == (cur.email or '').lower())
    if not allowed:
        messages.error(request, "You do not have permission to view this email.")
        return redirect('messages.email_inbox')

    # find root of thread
    root = email
    while root.parent:
        root = root.parent

    # collect thread messages and compute depths
    collected = _collect_thread(root)
    messages_list = []
    for msg_obj, depth in collected:
        messages_list.append({
            'id': msg_obj.id,
            'sender': msg_obj.sender,
            'sender_email': msg_obj.sender_email,
            'recipient_email': msg_obj.recipient_email,
            'recipient_user': msg_obj.recipient_user,
            'subject': msg_obj.subject,
            'body': msg_obj.body,
            'timestamp': msg_obj.timestamp,
            'depth': depth,
        })

    # mark messages as read where this user is the recipient
    to_mark = EmailMessage.objects.filter(root_id:=root.id) if False else None
    # fallback marking: mark any in thread where recipient_user is current user or recipient_email matches
    for mobj, _d in collected:
        if mobj.recipient_user == cur or (mobj.recipient_email and (cur.email and mobj.recipient_email.lower() == cur.email.lower())):
            if not mobj.read:
                mobj.read = True
                mobj.save(update_fields=['read'])

    # prepare reply defaults: use user.email if sender is a User, otherwise fall back to sender_email
    original_sender_email = email.sender.email if email.sender and getattr(email.sender, 'email', None) else email.sender_email
    root_subject = root.subject

    return render(request, 'home/email_view.html', {
        'messages_list': messages_list,
        'template_data': {'title': f'Thread: {root_subject}'},
        'root_id': root.id,
        'original_sender_email': original_sender_email,
        'root_subject': root_subject,
    })


@login_required
def thread_view(request, user_id):
    # show full internal message thread between request.user and user_id
    try:
        partner = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('messages.index')

    if partner == request.user:
        messages.error(request, "Cannot view a thread with yourself.")
        return redirect('messages.index')

    # collect messages between the two users, ordered oldest->newest
    thread_msgs = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=partner)) | (Q(sender=partner) & Q(recipient=request.user))
    ).order_by('timestamp')

    # mark unread messages where partner sent to current user
    unread = thread_msgs.filter(sender=partner, recipient=request.user, read=False)
    if unread.exists():
        unread.update(read=True)

    # prepare messages_list for template
    messages_list = []
    for m in thread_msgs:
        messages_list.append({
            'id': m.id,
            'sender': m.sender,
            'recipient': m.recipient,
            'subject': m.subject,
            'body': m.body,
            'timestamp': m.timestamp,
        })

    initial_subject = ''
    if thread_msgs.exists():
        # default reply subject
        initial_subject = 'Re: ' + thread_msgs.first().subject if thread_msgs.first().subject else ''
        # identify the most recent message id to use as parent for replies
        last_msg = thread_msgs.last()
        parent_id = last_msg.id if last_msg else None

    return render(request, 'home/message_thread.html', {
        'partner': partner,
        'messages_list': messages_list,
        'initial_subject': initial_subject,
        'parent_id': parent_id,
    })