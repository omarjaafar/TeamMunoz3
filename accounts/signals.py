from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import Profile, CandidateSavedSearch, CandidateSearchNotification, apply_candidate_querystring_filters

@receiver(post_save, sender=Profile)
def notify_candidate_saved_search_matches(sender, instance: Profile, created, **kwargs):
    # Only consider job seekers
    if instance.role != "JOB_SEEKER":
        return

    # Single-profile queryset to test matching
    prof_qs = Profile.objects.filter(pk=instance.pk)

    # Recruiters' saved searches (exclude candidate themself if accounts share user table)
    searches = CandidateSavedSearch.objects.exclude(recruiter=instance.user)

    for ss in searches:
        # Optional: avoid noisy re-mails on minor edits (skip if not new and already checked after last change)
        # If you track updated_at on Profile, prefer that; else always consider
        matched = apply_candidate_querystring_filters(prof_qs, ss.querystring).exists()
        if matched:
            notif, made = CandidateSearchNotification.objects.get_or_create(saved_search=ss, candidate=instance)
            if made and ss.email_enabled and ss.recruiter.email:
                send_mail(
                    subject=f"New candidate match: {instance.user.get_full_name() or instance.user.username}",
                    message=(
                        f"A candidate matches your saved search '{ss}':\n\n"
                        f"{instance.headline or ''}\n"
                        f"Skills: {instance.skills or ''}\n"
                        f"Location: {getattr(instance, 'location', '')}\n"
                        f"Open the app to view the profile."
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[ss.recruiter.email],
                    fail_silently=True,
                )

        ss.last_checked = timezone.now()
        ss.save(update_fields=["last_checked"])