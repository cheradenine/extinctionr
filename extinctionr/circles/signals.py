import os.path
from django.db.models.signals import m2m_changed, post_save
from django.conf import settings

from django.dispatch import receiver
from crum import get_current_user

from .models import (
    Circle, CircleMember, MembershipRequest, 
    CircleJob, Signup, Contact
)
from . import comm, git, get_circle
from .anapi import add_to_action_networks


@receiver(post_save, sender=MembershipRequest)
def sent_pending_email(sender, instance, **kwargs):
    if not instance.confirmed_by:
        comm.notify_circle_membership(instance.circle, 'pending member', [instance.requestor_id])


@receiver(post_save, sender=CircleMember)
def send_join_email(sender, instance, **kwargs):
    comm.notify_circle_membership(instance.circle, instance.role, [instance.contact_id])


@receiver(post_save, sender=Circle)
def save_to_git(sender, instance, **kwargs):
    current_user = get_current_user()
    if current_user:
        committer = "{} <{}>".format(current_user, current_user.email).encode('utf8')
        repo_dir = os.path.join(settings.STATIC_ROOT, 'circle_history')
        git.commit_circles_to_git(repo_dir, committer)


@receiver(post_save, sender=CircleJob)
def notify_job(sender, instance, **kwargs):
    if instance.filled:
        comm.notify_circle_job(instance)


@receiver(post_save, sender=Signup)
def send_signup_email(sender, instance, **kwargs):
    outreach_circle = get_circle('outreach')
    if outreach_circle:
        comm.notify_new_signup(outreach_circle, instance)


@receiver(post_save, sender=Contact)
def send_contact_to_action_networks(sender, instance, **kwargs):
    contact = instance
    add_to_action_networks(contact)


